def calcBPM(avg,threshold,prevValue,lastBeatTime,bpm):
    if prevValue<threshold and avg>=threshold:
        now=time.ticks_ms()
        diff=time.ticks_diff(now,lastBeatTime)
        if diff>0:
            bpm=60000/diff
            print(int(bpm))
        lastBeatTime=now
    return avg,lastBeatTime,bpm