# -*- coding: utf-8 -*-
"""
This file contains utilities to simplify Binance investment wrapper script.

Created on Sat Jun 26 10:28:53 2021

@author: boris
"""

import decimal
import math

class Utilities:
    """
    Utilities is a class that contains different methods to simplify crypto_wrapper.py
    """
    def price_round(self, price, isCeiled):
        """
        Method that either rounds a float to two decimals if the float is superior to 0.1 or
        rounds it to two digits after the first non-zero decimal.
        price : Float to be rounded
        isCeiled : Boolean variable to defined whether the variable should be rounded down (0) or up (1)
        @return rounded float
        """
        val = self.float_to_str(price)
        parts = val.split(".")
        if price >= 0.1 or val == "0":
            if isCeiled:
                return math.ceil(price*100) / 100.0
            else:
                return math.floor(price*100) / 100.0
        else:
            countZeros = 0
            for i in range(len(parts[1])):
                c = parts[1][i]
                if c == '0':
                    countZeros += 1
                else:
                    break;
            if isCeiled:
                return math.ceil(price*10**(2+countZeros)) / 10**(2+countZeros)
            else:
                return math.floor(price*10**(2+countZeros)) / 10**(2+countZeros)

    def round_float(self, val, decimal, isCeiled):
        """
        Method that either rounds up or rounds down a floating number based on the user-specified
        place.
        val : Float to be rounded
        decimal : Integer that specifies the place of the rounding
        isCeiled : Boolean variable to define whether the variable should be rounded down (0) or up (1)
        @return rounded float
        """
        if isCeiled:
            return math.ceil(val*10**decimal) / (10**decimal)
        else:
            return math.floor(val*10**decimal) / (10**decimal)

    def float_to_str(self, f):
        """
        Method that converts the given float to a string, without resorting to scientific
        notation.
        """
        # create a new context for this task
        ctx = decimal.Context()
        # 20 digits should be enough for everyone :D
        ctx.prec = 20
        d1 = ctx.create_decimal(repr(f))
        return format(d1, 'f')
