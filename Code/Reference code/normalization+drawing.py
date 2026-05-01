def drawNdata(dataSource,minMax):
    x=-1
    index=-1
    lastPos=(0,0)
    summ=0
    threshold=30
    prevValue=0
    lastBeatTime=time.ticks_ms()
    bpm=0
    while index<1000:
        data=dataSource.get()
        if dataSource.has_data():
            index+=1
            nData=63-((data-minMax[0])/(minMax[1]-minMax[0])*63)
            summ+=int(nData)
            if index%8==0:
                avg=summ/8
                if avg>63:
                    avg=63
                elif avg<0:
                    avg=0
                avg,lastBeatTime,bpm=calcBPM(avg,threshold,prevValue,lastBeatTime,bpm)
                prevValue=avg
                x+=1
                oled.pixel(x,int(avg),1)
                oled.line(lastPos[0],lastPos[1],x,int(avg),1)
                oled.fill_rect(x+1,0,2,64,0)
                oled.show()
                lastPos=(x,int(avg))
                summ=0
            if index==999:
                oled.fill_rect(0,0,2,63,0)
                lastPos=(0,0)
                index=0
                x=0
            elif index%250==0:
                minMax=getMinMax(dataSource)