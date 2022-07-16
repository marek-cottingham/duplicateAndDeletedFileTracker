from duplicateAndDeletedFileTracker import queries
from duplicateAndDeletedFileTracker.config import config
from duplicateAndDeletedFileTracker.main import openConnection

while(True):
    print("WARNING This will delete ALL archive data in database:")
    print(config.connect["dbname"])
    print("Continue [N / Y]?")
    x = input(">>>")
    if x == "N":
        exit()
    if x == "Y":
        break

with openConnection(config.connect) as cursor:
    cursor.execute(queries.resetAllTables)
    cursor.execute(queries.resetViewAndProcs)