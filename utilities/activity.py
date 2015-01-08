#!/usr/bin/env python

import popen2, datetime

from PyQt4.QtCore import *
from PyQt4.QtGui import *

if __name__ == "__main__":

    so, si = popen2.popen2("hg log")
    si.close()
    lines = filter(lambda line: line.startswith("date:"), so.readlines())
    
    dates = map(lambda line: line.split()[2:4] + line.split()[5:6], lines)
    datetimes = map(lambda date: datetime.datetime.strptime(" ".join(date), "%b %d %Y"), dates)
    datetimes.reverse()
    
    start = datetimes[0]
    finish = datetimes[-1]
    
    activity = {}
    m = 0
    for d in datetimes:
        activity[d] = activity.get(d, 0) + 1
        m = max(m, activity[d])
    
    app = QApplication([])
    baseline = (m * 10)
    height = baseline + 32
    image = QImage((finish - start).days, height, QImage.Format_RGB16)
    image.fill(Qt.white)
    
    p = QPainter()
    p.begin(image)
    year = datetimes[0].year
    
    fm = QFontMetrics(p.font())
    
    d = start
    while d <= finish:
    
        x = (d - start).days
        
        if d in activity:
            size = activity[d]*10
            top = baseline - size
            p.fillRect(x, top, 1, size, Qt.red)
        
        if d.year != year:
            p.drawLine(x, baseline, x, height)
            width = fm.width(str(year))
            p.drawText(QRect(x - width - 8, baseline, width, 32),
                       Qt.AlignCenter, str(year))
            year = d.year
            width = fm.width(str(year))
            p.drawText(QRect(x + 8, baseline, width, 32),
                       Qt.AlignCenter, str(year))
        
        d += datetime.timedelta(days = 1)
    
    p.drawLine(0, baseline, (finish - start).days, baseline)
    p.end()
    image.save("Castle-Raider-activity.png")
