# fp_to_string
#
# Floating point to string functions
#
# Available modes are "s" - 32-bit, "d" - 64-bit, "ed" - 80-bit, and "q" - 128-bit

# Data for fp_to_string
mode_data = {
    #       data  exp.  man.  imp.
    #       size  size  size   one
    "s"  : ( 32L,   8L,  23L,   1L),
    "d"  : ( 64L,  11L,  52L,   1L),
    "ed" : ( 80L,  15L,  64L,   0L),
    "q"  : (128L,  15L, 112L,   1L)
    }

def fp_conv_common(mode, binary):
    (size, exp_size, man_size, imp_one) = mode_data[mode]
    unbiased_exp = ((binary >> man_size) & ((1L << exp_size) - 1L))
    exp =  unbiased_exp - ((1L << (exp_size - 1L)) - 1L)
    if unbiased_exp == 0 and imp_one:
        # subnormal, add one to the exponent
        exp = exp + 1
    man = (binary & ((1L << man_size) - 1L))
    if ((binary >> man_size) & ((1L << exp_size) - 1L)):
        man |= (imp_one << man_size)
    sign = (binary >> (size - 1)) & 1
    
    # Check for NaNs
    nan = None
    if ((binary >> man_size) & ((1L << exp_size) - 1L)) == ((1L << exp_size) - 1L):
        if (binary >> (man_size - 1L)) & 1L:
            nan = "QNaN"
        else:
            if binary & ((1L << man_size) - 1L):
                nan = "SNaN"
            else:
                if sign:
                    nan = "-Inf"
                else:
                    nan = "+Inf"
    return (size, exp_size, man_size, imp_one, exp, man, sign, nan)

def fp_to_binstring(mode, binary):
    binary = long(binary)
    (size, exp_size, man_size, imp_one, exp, man, sign, nan) = fp_conv_common(mode, binary)
    if nan != None:
        return nan

    if sign:
        ret = "-"
    else:
        ret = "+"

    if man & (1L << man_size):
        ret = ret + "1."
    else:
        ret = ret + "0."

    for c in range(man_size-1,-1,-1):
        if man & (1L << c):
            ret = ret + "1"
        else:
            ret = ret + "0"

    ret = ret + " * 2^(%d)" % (exp)

    return ret


# Converts the binary representation of floating point values to strings with num_digits precision.
def fp_to_string(mode, binary, num_digits):
    # Get all the needed data
    binary = long(binary)
    num_digits = long(num_digits)

    (size, exp_size, man_size, imp_one, exp, man, sign, nan) = fp_conv_common(mode, binary)

    if nan != None:
        return nan

    # Set up the numerator and denominator
    if exp >= 0L:
        numer = man << exp
        denom = 1L << (man_size - 1 + imp_one)
    else:
        numer = man
        denom = 1L << (man_size - 1 + imp_one) << -exp

    # Calculate the exponent
    expon = 0L
    if man != 0L:
        adj1 = 10L
        adj2 = 1L
        while adj1 != 1:
            if denom / numer * 10 >= adj1:
                numer *= adj1
                expon -= adj2
                adj1 *= 10L
                adj2 += 1L
            else:
                adj1 /= 10L
                adj2 -= 1L
        adj1 = 10L
        adj2 = 1L
        while adj1 != 1:
            if numer / denom >= adj1:
                numer /= adj1
                expon += adj2
                adj1 *= 10L
                adj2 += 1L
            else:
                adj1 /= 10L
                adj2 -= 1L
    
    # Calculate the digits
    digits = []
    for i in range(0L, num_digits):
        # Calculate the digit
        digits += [numer / denom]
        numer = (numer % denom) * 10

        # Round last digit
        if (i == num_digits - 1) and (numer / denom >= 5):
            j = num_digits - 1
            while 1:
                digits[j] += 1
                if digits[j] == 10:
                    digits[j] = 0
                    if i == 0:
                         digits = [0] + digits
                         expon += 1
                    else:
                        j -= 1
                else:
                    break;

    # Convert to string
    if sign:
        result = "-"
    else:
        result = " "
    result += "%i." % digits[0]
    for digit in digits[1:]:
        result += "%i" % digit
    if expon >= 0:
        result += "e+%i" % expon
    else:
        result += "e%i" % expon
    
    return result


# Like fp_to_string, but pads the string with spaces to the specified width.
def fp_to_string_fixed(mode, binary, num_digits, width):
    result = fp_to_string(mode, binary, num_digits)
    while len(result) < width:
        result += " "
    return result
