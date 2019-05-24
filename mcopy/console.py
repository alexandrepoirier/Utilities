"""
console.py
last modified : 4 april 2015

Some utility functions used with the terminal.
"""

def getTerminalSize():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMS', 80))
    return (int(cr[1]), int(cr[0]))
    
def colour(text, colour):
    colours = {'black':"[0;30m",
               'blue':"[0;34m",
               'green':"[0;32m",
               'cyan':"[0;36m",
               'red':"[0;31m",
               'purple':"[0;35m",
               'brown':"[0;33m",
               'orange':"[0;33m",
               'light gray':"[0;37m",
               'dark gray':"[1;30m",
               'light blue':"[1;34m",
               'light green':"[1;32m",
               'light cyan':"[1;36m",
               'light red':"[1;31m",
               'light purple':"[1;35m",
               'yellow':"[1;33m",
               'white':"[1;37m"}
    
    if colour not in colours:
        return text
    return '\033'+colours[colour]+text+'\033[0m'

class ProgressBar:
    def __init__(self, min, max, width):
        self._min = min
        self._max = max
        self._range = float(max-min)
        self._width = width-2
        self._progress_bar_str = "[]"
        self.update(self._min)
        
    def __str__(self):
        return self._progress_bar_str
        
    def update(self, value):
        self._value = value
        if value < self._min: self._value = self._min
        if value > self._max: self._value = self._max
        
        done = int(self._value/self._range*self._width)
        togo = self._width - done
        
        temp = "[" + "#"*done + " "*togo + "]"
        
        percent = " " + str(int(self._value/self._range*100)) + "% "
        percentStart = int(self._width/2) - len(percent)
        percentEnd = percentStart+len(percent)
        
        self._progress_bar_str = temp[:percentStart] + percent + temp[percentEnd:]
        
    def setMin(self, min):
        self._min = min
        self._range = float(self._max-min)
        self.update(self._value)
        
    def setMax(self, max):
        self._max = max
        self._range = float(max-self._min)
        self.update(self._value)
        
    def setWidth(self, width):
        self._width = width-2
        self.update(self._value)
        
if __name__ == "__main__":
    p = ProgressBar(0,15,80)
    print(str(p))
    p.update(5)
    print(str(p))
    p.update(10)
    print(str(p))
    p.update(15)
    print(str(p))