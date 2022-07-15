from archiveDatabase import queries
from archiveDatabase.config import config
from archiveDatabase.main import openConnection

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