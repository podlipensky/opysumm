import os


def etime():
    """See how much user and system time this process has used so far and return the sum."""
    user, sys, chuser, chsys, real = os.times()
    return user+sys

def print_etime(start):
    end = etime()
    print "time:", str(end - start)