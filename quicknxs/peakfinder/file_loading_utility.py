import numpy as np

def loadCsvFile(filename):
    '''
    Loading CSV file created with Excel to test PeakFinderDerivation algorithm
    '''
    f = open(filename, 'rt')
    data = f.readlines()
    data  = data[0].split('\r')
    final_data = []
    for row in data:
        _row_split = row.split(',')
        final_data.append(_row_split)
    f.close()
    final_data = convertArrayToFloat(final_data)
    [x,y,e] = isolateXYE(final_data)
    return [x,y,e]

def isolateXYE(data_array):
    x, y, e = [],[],[]
    for _row in data_array:
        x.append(_row[0])
        y.append(_row[1])
        e.append(_row[2])
    return [x,y,e]

def convertArrayToFloat(data_array):
    final_array = []
    for _row in data_array:
        [x,y,e] = [float(_row[0]), float(_row[1]), float(_row[2])]
        final_array.append([x,y,e])
    return final_array

if __name__ == '__main__':
    filename = 'peakfinder/easy_data_set.csv'
    [x,y,e] = loadCsvFile(filename)
    print x
