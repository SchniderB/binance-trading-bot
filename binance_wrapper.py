# -*- coding: utf-8 -*-
"""
This script is a wrapper that runs all the functions that constitute the trading
bot.

Created on Sat Jul 20 15:28:53 2021

@author: boris
"""

# Request rate limit: 20 request per second, 1200 requests per minute, 10 orders per second

#### Import built-in and third-party modules and packages ####
from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
import time
import datetime
import math
import os
import sys
####

#### Import home-made modules and packages ####
from util.trade_manager import Trade_manager
from util.utilities import Utilities
# import API.update_database  # Module to write the trading results into a local database
####

#### Pre-defined parameters ####
with open("config.txt", "r") as config:
    benefit = float(config.readline().rstrip("\n").rstrip("\r").split("\t")[1])
    recovery = str(config.readline().rstrip("\n").rstrip("\r").split("\t")[1]).lower()
####

#### Get all the currency pair names ####
currencies = ["BTC", "ETH", "BNB", "ADA", "DOT"]
base_currency = "USDT"
all_pairs = ["{}{}".format(currency, base_currency) for currency in currencies]
USDT_balance = 200.0
crypto_details = {pair:[0, 0.0, 0.0015] for pair in all_pairs}  # ID : [decimal, minimal order volume, fee]
crypto_details["last_extraction_time"] = 0.0
isStart = True
minOrder = 0.0001
currency_balance = {currency : "0" for currency in currencies}  # Used to store the balance per currency
####

#### Define base variables and instanciate classes ####
with open("binance.key", "r") as keys:
    api_key = keys.readline().rstrip("\n").rstrip("\r")
    api_secret = keys.readline().rstrip("\n").rstrip("\r")
binance_client = Client(api_key, api_secret)
utilities = Utilities()
trade_manager = Trade_manager(currencies=all_pairs, benefit=benefit, minOrder=minOrder)
# update = API.update_database.Update_DB()  # Module to write the trading results into a local database
####

#### Recovery system and write output file ####
trade_history = []
list_data = os.listdir("data/")
if recovery == "true":
    for file in list_data:
        if file == "trade_history.txt":
            with open("data/{}".format(file), "r") as f:
                for line in f:
                    trade = {it.split(":")[0] : it.split(":")[1] for it in line.rstrip("\n").rstrip("\r").split("\t")}
                    trade["orderId"] = int(trade["orderId"])  # Necessary to convert the values that will be used into their suitable type
                    trade["time"] = int(trade["time"])  # Necessary to convert the values that will be used into their suitable type
                    trade_history.append(trade)
        elif file == "USDT_balance.txt":
            with open("data/USDT_balance.txt".format(file), "r") as f:
                USDT_balance = float(f.readline())
else:
    if not list_data:  # Only write if no files are present to avoid overwriting
        for currency in currencies:
            with open("data/{}_records.txt".format(currency), "w") as balance_file:
                balance_file.write("round\ttime\toperation\torder_price\tdecimal\tfee\tmin_order_volume\tvolume_to_invest\t{0}_balance\t{1}_balance\t{1}_rate\ttimestamp\tbenefit\tclosed_order_name\n".format(base_currency, currency))
    else:
        print("ERROR: data folder not empty. Please empty the folder or add TRUE in the config file next to RECOVERY to start in recovery mode.")
        exit()
####

#### Generate log file ####
with open("data/error.log", "w") as err_file:
    err_file.write("Please find the list of errors below:\n")
####

#### Start investment loop ####
loop_nb = 0
while True:

    try:
        #### Define loop variables ####
        loop_nb += 1  # Start at loop #1
        all_orders = {}
        current_time = time.time()
        ####

        #### Extract all prices ####
        try:
            prices = {pair["symbol"] : float(pair["price"]) for pair in binance_client.get_all_tickers() if pair["symbol"] in all_pairs}
        except Exception as E:
            with open("data/error.log", "a") as err_file:
                err_file.write("Price extraction failed. The following error arose and the current loop was skipped: {}\n".format(E))
            time.sleep(0.3)
            continue
        trade_manager.set_prices(prices=prices)  # Update the details in the instance once a day
        ####

        #### Extract decimal, minimal order volume and fee ####
        if current_time > crypto_details["last_extraction_time"] + 3600*24:  # Update only once a day
            try:
                for pair in all_pairs:
                    symbol_info = binance_client.get_symbol_info(pair)
                    for f in symbol_info["filters"]:
                        if f["filterType"] == "LOT_SIZE":
                            crypto_details[pair][0] = int(round(abs(math.log(float(f["stepSize"]), 10)), 0))
                            crypto_details[pair][1] = float(f["minQty"])
                            # For now the fee rate is hardcoded
                            crypto_details["last_extraction_time"] = current_time  # Update current time only if values were found for decimal and min volume
                    trade_manager.set_details(crypto_details=crypto_details)  # Update the details in the instance once a day
            except Exception as E:
                with open("data/error.log", "a") as err_file:
                    err_file.write("Detail extraction failed for {}. The following error arose and the current loop was skipped: {}\n".format(pair, E))
                time.sleep(0.3)
                continue
        ####

        #### Extract current order list ####
        try:
            for pair in all_pairs:
                for ord in binance_client.get_all_orders(symbol=pair):  # [{'symbol': 'BTCUSDT', ..., 'status': 'FILLED'}, {'symbol': 'BTCUSDT', ..., 'status': 'NEW'}, {'symbol': 'ADAUSDT', ..., 'status': 'FILLED'}, ...]
                    if ord["symbol"] == pair:
                        all_orders[ord["orderId"]] = ord
                time.sleep(0.3)
        except Exception as E:
            with open("data/error.log", "a") as err_file:
                err_file.write("Order extraction failed for {}. The following error arose and the current loop was skipped: {}\n".format(pair, E))
            time.sleep(0.3)
            continue
        if isStart:
            trade_manager.ignore_history(all_orders=all_orders)  # Method that just makes sure the ID of all the previous orders are not considered as new
            if recovery == "true":
                trade_manager.recover_history(trades=trade_history)
        # print(crypto_details)
        ####

        #### Trade manager ####
        print("*********")
        print("LOOP: {}".format(loop_nb))
        print("ALL ORDERS: ")
        print("\tsymbol\torderId\tprice\torigQty\texecutedQty\tstatus\tside\ttime")
        for ord_id in all_orders.keys():
            print("\t", [all_orders[ord_id]["symbol"], all_orders[ord_id]["orderId"], all_orders[ord_id]["price"], all_orders[ord_id]["origQty"], all_orders[ord_id]["executedQty"], all_orders[ord_id]["status"], all_orders[ord_id]["side"], all_orders[ord_id]["time"]])
        print("PRICES: ", prices)
        print("BALANCE 1: ", USDT_balance)
        new_trades = trade_manager.new_trades(base_available=USDT_balance)  # Define all new possible trades with money available
        print("NEW TRADES 1: ", new_trades)
        new_trades, trades_to_cancel, USDT_balance, filled_trades = trade_manager.verify_orders(all_orders=all_orders, prices=prices, new_trades=new_trades, base_available=USDT_balance)  # Verify which pending orders should be closed, created or cancelled
        print("NEW TRADES 2: ", new_trades)
        print("TRADES TO CANCEL: ", trades_to_cancel)
        print("BALANCE 2: ", USDT_balance)
        print("DETAILS: ", crypto_details)
        print("*********")
        ####

        #### Create and cancel orders ####
        for new_trade in new_trades:
            print(new_trade)
            try:
                binance_client.create_order(symbol=new_trade[0], side=new_trade[3], type="LIMIT",
                timeInForce="GTC", quantity=new_trade[2], price=str(new_trade[1]))  # GTC stands for Good Till Canceled
            except Exception as E:
                with open("data/error.log", "a") as err_file:
                    err_file.write("An error occurred when creating the order [symbol={}, side={}, quantity={}, price={}]. Please make sure to verify that the trade was created. If not, please correct the USDT balance in the file USDT_balance.txt if the failed order was a BUY order, or make sure to manually create a SELL trade if the failed order was a SELL order. The following error arose: {}\n".format(str(new_trade[0]), str(new_trade[3]), str(new_trade[2]), str(new_trade[1]), E))
                continue
            time.sleep(0.3)

        # # Canceled orders
        for trade in trades_to_cancel:
            try:
                binance_client.cancel_order(symbol=trade[0], orderId=trade[1])
            except Exception as E_cancel:
                with open("data/error.log", "a") as err_file:
                    err_file.write("Cancelling trade {} {} failed. The following error arose and the cancellation was skipped: {}\n".format(str(trade[0]), str(trade[1]), E_cancel))
                continue
            time.sleep(0.2)
        ####

        #### Extract balance per crypto and for USDT, compute total balance ####
        total_bal = USDT_balance  # Replace the total value by the USDT balance
        for i, currency in enumerate(currencies):
            try:
                currency_balance[currency] = binance_client.get_asset_balance(asset=currency)["free"]
            except Exception as E:
                currency_balance[currency] = ""
                with open("data/error.log", "a") as err_file:
                    err_file.write("Failed to extract the balance of {}. The following error arose and the balance was consequently set to 0: {}\n".format(currency, E))
                continue
            if currency_balance[currency]:
                total_bal += float(currency_balance[currency])*prices[all_pairs[i]]  # Convert balance into value in USDT
            else: currency_balance[currency] = "0"
            time.sleep(0.3)
        ####

        #### Write results to file ####
        for trade in filled_trades:
            with open("data/{}_records.txt".format(trade["symbol"].rstrip(base_currency)), "a") as balance_file:
                balance_file.write("{}\n".format("\t".join([str(loop_nb), str(datetime.datetime.fromtimestamp(trade["time"]/1000)), trade["side"], str(trade["price"]), str(crypto_details[trade["symbol"]][0]), str(crypto_details[trade["symbol"]][2]), str(crypto_details[trade["symbol"]][1]), str(trade["executedQty"]), str(USDT_balance), currency_balance[trade["symbol"].rstrip(base_currency)], str(prices[trade["symbol"]]), str(total_bal), str(trade["time"]/1000), str(trade["orderId"])])))
        ####

        #### Save trade_manager self.trades and USDT balance to a file ####
        if trade_manager.trades:
            with open("data/trade_history.txt", "w") as hist:
                for trade in trade_manager.trades:
                    hist.write("{}\n".format("\t".join(["{}:{}".format(str(it[0]), str(it[1])) for it in trade.items()])))
        with open("data/USDT_balance.txt", "w") as bal:
            bal.write(str(USDT_balance))
        ####

        #### Update API ####
        # The code below is to store the trading results in a local database
        # try:
        #     update.update_trades2("data")
        #     update.update_prices2("data")
        # except Exception as E:
        #     with open("data/error.log", "a") as err_file:
        #         err_file.write("ERROR with the DB update: {}\n".format(str(E)))
        ####

        #### Define wait time ####
        isStart = False
        time.sleep(20)
        ####

    #### Define general exception ####
    except Exception as E:
        with open("data/error.log", "a") as err_file:
            err_file.write("ERROR: {}\n".format(str(E)))
    ####

#### End investment loop ####
