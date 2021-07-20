# Instructions to use a Python trading bot with Binance

## Aim of the project
This project presents how to make and run a trading bot coded fully in Python based on Binance API. The trading bot should 
be able to buy and sell a predefined list of cryptocurrencies for you on your Binance account. The trading bot tries to buy 
cryptocurrencies at lower prices than the market prices and sells them when they are higher. The trading algorithm relies solely 
on the current price and does not include external indicators. The trading is based on a single base currency, such as the `USDT`, 
and does not directly swap coins between each other.

## Disclaimer
This is an educational project, not a real investment strategy or advice, and I take no responsibility for any financial 
losses or misuse of this code. If you use this code, ensure you keep your API keys secure and never enable fund 
withdrawal permissions. Please note that the algorithm only performs well during bullish periods due to the significant 
daily price fluctuations it can exploit. I strongly advise not to use it at the end of a bull run as it will likely buy 
overpriced cryptocurrencies.

## Dependencies
### Requirements
- Python 3.6 or Higher
- Binance Python API client `python-binance` (set-up described below)
- Binance API key with the permissions to read the user's balance, create, modify and delete buy and sell orders
- Script `binance_wrapper.py`
- Folder `data`
- Configuration file `config.txt`

### First set-up
1. Install `virtualenv` if it is not already installed
```bash
pip install virtualenv
```
2. Create virtual environment in your folder of interest
```bash
virtualenv python-binance
```
3. Activate the virtual environment
```bash
source python-binance/bin/activate
```
4. Install the libraries of interest in the virtual environment based on the `requirements.txt` file
```bash
pip install -r requirements.txt
```

### Reactivate the virtual environment each time you need to use the trading bot
```bash
source python-binance/bin/activate
```

## Account permissions
### Balance-reading and order API key
You will need an API key from your Binance account with ONLY (!IMPORTANT!) balance-reading, order creation, order 
modification and order deletion permissions. Save the public and secret keys on the first and second lines, respectively, 
in a local file named `binance.key`. The process to generate the key can be found directly in Binance FAQs and tutorials 
which are quite clear and simple.


## Settings and requirements
### Base currency selection
You will need to specify the base currency as the value of the variable `base_currency` in the script `binance_wrapper.py` 
which is set to `USDT` by default.

### List of cryptocurrencies
You can define the list of cryptocurrencies you want the trading bot to speculate on with the variable `currencies` in the 
script `binance_wrapper.py`.

### Minimal balance
The trading bot might not work if your starting base currency balance is inferior to 150 `USDT`.

### Configuration file
The configuration file can be used with different parameters. The parameters should be separated from their values with a 
tab. Here is how the parameters can be used:
* `BENEFIT`: Floating point (i.e. decimal number) of the percentage you want to buy your cryptocurrencies below their current price.
* `RECOVER`: If set to `TRUE`, the file `data/trade_history.txt` is used to recover your trade history. It will also recover
  your base currency balance based on the file `data/USDT_balance.txt`. I recommend to use this argument only if you want to
  recover the data of a previous run of this trading bot.

The default content of `config.txt` is:
```bash
BENEFIT	0.01
RECOVERY	TRUE
```

### Default algorithm settings
The following settings should be modified for your custom use:
- `BENEFIT`: Percentage under which you will buy the selected cryptocurrencies. Default 0.01 (i.e. 1%). E.g. if the `BTC` 
is in your list of currencies, a buy trade will be set at 99% of its current price. Upon completion, a sell trade will 
immediately be set at the initial `BTC` price, i.e. in this case your buy price + 1%.
- `USDT_balance`: The base currency balance you want to define as starting funds for the trading bot, so that it does not 
use all the balance available of that concerned base currency on your account


## Launch the cryptocurrency trading bot
A simple Python command will launch the trading bot:
```bash
python3 binance_wrapper.py
```
As the trading bot will run indefinitely, I recommend you run it in a detached terminal state. You can use the terminal 
multiplexer `Screen` for this purpose.


## Results
### Output files
All the output files are saved in the folder `data`:
- `$symbol_records.txt`: A file containing all decisions (`BUY` or `SELL`) and price statistics for each cryptocurrency 
symbol
- `trade_history.txt`: The most recent buy or sell trade for your selected cryptocurrencies will be saved in this file
- `USDT_balance.txt`: Last base currency balance obtained by the trading bot

### Performances
The algorithm seemed to work on Binance test net, but the low price buy trades would never be completed on the main net 
when the `BENEFIT` threshold was set too high in `config.txt`. The optimal strategy for this algorithm would be to launch 
it at the beginning of a bull run and to stop it before the end of the bull run and manually sell all the remaining 
cryptocurrencies.

## Project Timeline
- Start Date: April 2021
- Completion Date: July 2021
- Maintenance status: Inactive
