Feature: auto population of main table
    Given a set of runs,
    The program will sort them by decreasing lambda
    and increasing 2theta. 
    Runs with same parameters will be added together
    
Scenario: sor the data set
    Given the sequence of runs "127784-127790"
    Then the sorted list of files will be "127784,127785,127786,127787,1227788,127789,127790"
    
    