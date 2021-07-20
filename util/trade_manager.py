# -*- coding: utf-8 -*-
"""
This module is a trade manager.

Created on Sat Jul 20 15:28:53 2021

@author: boris
"""

from util.utilities import Utilities

class Trade_manager(Utilities):
    """
    Class Trade_manager that contains all the methods to run the trade manager.
    """
    def __init__(self, currencies, benefit, minOrder):
        self.trades = []  # contains all the details from all_orders
        self.trade_id = 1  # incremented value for the trade IDs
        self.currencies = currencies
        self.residual_trades = {currency : [] for currency in currencies}
        self.benefit = benefit
        self.total_invested_fraction = 0.1  # Invest % of the base available
        self.crypto_details = {}  # ID : [decimal, minimal order volume, fee]
        self.prices = {}  # ID : price
        self.order_id_history = []
        self.minOrder = minOrder
        print("*"*50)
        print("Currency pair: {}\nBenefit: {}%".format(",".join(currencies), str(benefit*100)))
        print("*"*50)

    def set_prices(self, prices):
        """
        Method that set the values for the price per pair.
        """
        self.prices = prices

    def set_details(self, crypto_details):
        """
        Method that set the values for the decimal, minimum volume order and
        fee per pair.
        """
        self.crypto_details = crypto_details

    def ignore_history(self, all_orders):
        """
        Method that adds all the previous orders to self.order_id_history so as to
        ignore them and not include them in self.trades.
        """
        for order_id in all_orders.keys():
            self.order_id_history.append(order_id)

    def recover_history(self, trades):
        """
        Method that re-generates self.trades based on the content of the previous run.

        :trades: list of dictionaries. Each dictionary contains the details of a trade
        """
        self.trades = trades

    def new_trades(self, base_available):
        """
        Method that verifies if funds are available for new BUY trades and if yes, that
        generates all the details necessary to make the new trades based on the crypto
        priority.

        Returns [[crypto_symbol, limit_price, volume, order_type]]
        """
        new_orders = []
        invested_value = self.total_invested_fraction * base_available
        for currency in self.currencies:
            if base_available >= invested_value and invested_value >= 11.0:
                volume = self.round_float(invested_value / self.prices[currency], self.crypto_details[currency][0], 0)  # 1: unrounded volume, 2: decimal place, 3: floor
                price = self.price_round(self.prices[currency] * (1-self.benefit) * (1-self.crypto_details[currency][2]), 0)
                if volume >= self.crypto_details[currency][1] and price*volume > self.prices["BTCUSDT"]*self.minOrder:  # If min volume is reached and min order size is reached
                    new_orders.append([currency, price, volume, "BUY"])
                    base_available -= invested_value
            else:
                break
        return new_orders

    def verify_orders(self, all_orders, prices, new_trades, base_available):
        """
        Method that verifies if:
        (1) BUY trades have been completed: provide details for SELL trade
        (2) BUY trades should be cancelled because the potential benefit has decreased or
        the price has increased further away from the limit and exceeds a realistic BUY
        threshold: provide the details to cancel BUY trade
        (3) New BUY trades defined with new_trades can actually be kept, if no BUY trade for
        the concerned cryptocurrency is pending
        (4) SELL trades have been completed: provide pair of BUY and SELL orders to remove
        from the list of current orders

        Returns list_of_trades_to_send, list_of_trades_to_cancel
        """
        #### Define output lists ####
        trades_to_send = []
        trades_to_cancel = []
        trades_to_remove = []  # List of IDs from self.trades of the trades to remove from self.trades
        returned_base = 0
        filled_trades = []
        ####
        print("ORDER HISTORY 1: ", self.order_id_history)
        print("TRADES 1: ")
        print("\tsymbol\torderId\tprice\torigQty\texecutedQty\tstatus\tside\ttime")
        for trade1 in self.trades:
            print("\t", [trade1["symbol"], trade1["orderId"], trade1["price"], trade1["origQty"], trade1["executedQty"], trade1["status"], trade1["side"], trade1["time"]])
        #### Add the new BUY and SELL trades from all_orders to self.trades
        for order_id in all_orders.keys():
            if not order_id in self.order_id_history:
                self.order_id_history.append(order_id)
                self.trades.append(all_orders[order_id])
                if all_orders[order_id]["status"] == "FILLED" or all_orders[order_id]["status"] == "PARTIALLY_FILLED":  # If new trade status is filled, make sure it appears as NEW in the list of trades so that the algorithm understands that a sell trade is necessary
                    self.trades[-1]["status"] = "NEW"
        ####

        # Check open trades in self.trades: (1) if BUY appears as canceled/rejected/expired, remove it from self.trades and += base_available,
        # (2) if BUY appears as filled, add new SELL trade and remove BUY, (3) if SELL appears as filled, remove
        # it from self.trades += base available, (4) if SELL appears as canceled/rejected/expired, replace it by the same SELL order
        for i, trade in enumerate(self.trades):
            if trade["side"] == "BUY":
                if all_orders.get(trade["orderId"]):
                    if all_orders[trade["orderId"]]["status"] == "CANCELED" or all_orders[trade["orderId"]]["status"] == "REJECTED" or all_orders[trade["orderId"]]["status"] == "EXPIRED":
                        trades_to_remove.append(trade["orderId"])
                        if trade["status"] == "PARTIALLY_FILLED":  # If the BUY trade was marked as partially_filled and that it was cancelled successfully, remove it from the list of trades + recover the money from cancellation + send trade for the partially_filled part of the buy trade
                            base_available += (float(all_orders[trade["orderId"]]["origQty"])-float(all_orders[trade["orderId"]]["executedQty"]))*float(all_orders[trade["orderId"]]["price"])*(1+self.crypto_details[all_orders[trade["orderId"]]["symbol"]][2])  # base_available should be increased with the unfilled part of the partial trade
                            filled_trades.append(all_orders[trade["orderId"]])  # Used to write the output file only
                            volume = float(all_orders[trade["orderId"]]["executedQty"])
                            price = self.price_round(float(trade["price"]) * (1+self.benefit/2) * (1+self.crypto_details[trade["symbol"]][2]), 0)
                            if volume >= self.crypto_details[trade["symbol"]][1] and price*volume > self.prices["BTCUSDT"]*self.minOrder:  # If min volume and min order size are reached send sell trade
                                trades_to_send.append([trade["symbol"], price, volume, "SELL"])  # Sell at the expected intial benefit
                            else:  # Partial trades that are too small to be sent as sell trades are grouped
                                self.residual_trades[trade["symbol"]].append([trade["symbol"], price, volume, "SELL"])
                        else:
                            base_available += float(trade["origQty"])*float(all_orders[trade["orderId"]]["price"])*(1+self.crypto_details[all_orders[trade["orderId"]]["symbol"]][2])  # base_available should be increased with the value of the canceled/rejected/expired trade
                    elif trade["status"] == "NEW" and all_orders[trade["orderId"]]["status"] == "FILLED":
                        trades_to_remove.append(trade["orderId"])
                        trades_to_send.append([trade["symbol"], self.price_round(float(trade["price"]) * (1+self.benefit/2) * (1+self.crypto_details[trade["symbol"]][2]), 0), all_orders[trade["orderId"]]["executedQty"], "SELL"])  # Sell at the expected intial benefit
                        filled_trades.append(all_orders[trade["orderId"]])  # Used to write the output file only
                else:  # if trade is present in the list of trades but not in all_orders which comes directly from binance, then delete it from self.trades
                    trades_to_remove.append(trade["orderId"])
            elif trade["side"] == "SELL":
                if all_orders.get(trade["orderId"]):
                    if all_orders[trade["orderId"]]["status"] == "CANCELED" or all_orders[trade["orderId"]]["status"] == "REJECTED" or all_orders[trade["orderId"]]["status"] == "EXPIRED":
                        trades_to_remove.append(trade["orderId"])
                        trades_to_send.append([trade["symbol"], trade["price"], trade["executedQty"], "SELL"])  # Sell at current price
                    elif trade["status"] == "NEW" and all_orders[trade["orderId"]]["status"] == "FILLED":
                        trades_to_remove.append(trade["orderId"])
                        base_available += float(all_orders[trade["orderId"]]["executedQty"])*float(all_orders[trade["orderId"]]["price"])*(1-self.crypto_details[all_orders[trade["orderId"]]["symbol"]][2])  # Sell at current price
                        filled_trades.append(all_orders[trade["orderId"]])  # Used to write the output file only
                else:  # if trade is present in the list of trades but not in all_orders which comes directly from binance, then delete it from self.trades and re-add it as a new sell trade
                    trades_to_remove.append(trade["orderId"])
                    trades_to_send.append([trade["symbol"], trade["price"], trade["origQty"], "SELL"])  # Sell at current price
        ####

        #### Remove the trades that need to be removed from self.trades ####
        self.trades = [trade for trade in self.trades if not trade["orderId"] in trades_to_remove]
        trades_to_remove = []
        ####

        #### Define a counter of NEW SELL trades per pair to avoid making new BUY trades as long as SELL trades are not filled ####
        counter = {}
        for trade in self.trades:
            if trade["status"] == "NEW" and trade["side"] == "SELL":
                if counter.get(trade["symbol"]):
                    counter[trade["symbol"]] += 1
                else:
                    counter[trade["symbol"]] = 1
        ####

        #### From self.trades, check if prices of BUY trades is still -benefit% below the current price (with a certain margin allowed in the gain direction)
        # remove all the BUY trades which are 'new' but not meeting this condition
        for trade in self.trades:
            if (trade["side"] == "BUY" and all_orders[trade["orderId"]]["status"] == "NEW") or (trade["side"] == "BUY" and trade["status"] == "NEW" and all_orders[trade["orderId"]]["status"] == "PARTIALLY_FILLED"):
                if self.prices[trade["symbol"]] * (1-self.benefit) < float(trade["price"]):  # if price has decreased cancel trade
                    trades_to_cancel.append([trade["symbol"], trade["orderId"]])
                    if all_orders[trade["orderId"]]["status"] == "PARTIALLY_FILLED":
                        trade["status"] = "PARTIALLY_FILLED"
                elif self.prices[trade["symbol"]] > float(trade["price"]) * (1+self.benefit * 2.5):  # If price > benefit x3.5, cancel BUY order
                    trades_to_cancel.append([trade["symbol"], trade["orderId"]])
                    if all_orders[trade["orderId"]]["status"] == "PARTIALLY_FILLED":
                        trade["status"] = "PARTIALLY_FILLED"
        ####

        #### From new_trades, verify the crypto that do not already have a BUY trade in self.trades and add a BUY trade
        # with the price suggested from new_trades
        for potential_trade in new_trades:
            isNew = True
            for trade in self.trades:
                if potential_trade[0] == trade["symbol"] and trade["side"] == "BUY":
                    isNew = False
            if isNew:  # If no BUY trade for the pair already opened
                if not counter.get(potential_trade[0]) or counter[potential_trade[0]] < 3:  # Only make new BUY trade if not already 3 open SELL trades
                    trades_to_send.append(potential_trade)
                    base_available -= potential_trade[1] * potential_trade[2] * (1+self.crypto_details[potential_trade[0]][2])
        ####

        #### Remove the trades that need to be removed from self.trades ####
        self.trades = [trade for trade in self.trades if not trade["orderId"] in trades_to_remove]
        ####

        #### Verify if residual trades can be combined to make a full sell trade ####
        for currency in self.currencies:
            volume = 0.0
            price = 0.0
            # if self.residual_trades[currency]:
            for trade in self.residual_trades[currency]:  # First time get full volume of currency available
                volume += trade[2]
            for trade in self.residual_trades[currency]:  # Second time use the full volume to average the prices in function of the intial volume
                price += trade[1] * (trade[2] / volume)
            volume = self.round_float(volume, self.crypto_details[currency][0], 0)
            price = self.price_round(price, 0)
            if volume >= self.crypto_details[currency][1] and price*volume > self.prices["BTCUSDT"]*self.minOrder:
                trades_to_send.append([currency, price, volume, "SELL"])
                self.residual_trades[currency] = []  # If the sum of the residuals reaches the minimal volume and order size, empty the residual trades
        ####

        print("ORDER HISTORY 2: ", self.order_id_history)
        print("TRADES 2: ")
        print("\tsymbol\torderId\tprice\torigQty\texecutedQty\tstatus\tside\ttime")
        for trade1 in self.trades:
            print("\t", [trade1["symbol"], trade1["orderId"], trade1["price"], trade1["origQty"], trade1["executedQty"], trade1["status"], trade1["side"], trade1["time"]])
        #### Return new BUY and SELL trades, trades to cancel and updated base available ####
        return trades_to_send, trades_to_cancel, base_available, filled_trades
        ####
        # All possible order status: canceled, expired, filled, new, partially_filled, pending_cancel, rejected
