currentFiles_expected_tables = {
    'alpha\\new_isDup.txt': {
        'duplicateFiles': True,
        'movedFiles': False,
        'newUnseenFiles': False,
        'modifiedFiles': False
    },
    'alpha\\bravo\\new.txt': {
        'duplicateFiles': False,
        'movedFiles': False,
        'newUnseenFiles': True,
        'modifiedFiles': False
    },
    'foxtrot\\movedFile.txt': {
        'duplicateFiles': False,
        'movedFiles': True,
        'newUnseenFiles': False,
        'modifiedFiles': False
    },
    'foxtrot\\movedWithNewAtOrginalLoc.txt': {
        'duplicateFiles': False,
        'movedFiles': True,
        'newUnseenFiles': False,
        'modifiedFiles': False
    },
    'alpha\\bravo\\modified.txt': {
        'duplicateFiles': False,
        'movedFiles': False,
        'newUnseenFiles': False,
        'modifiedFiles': True,
        'modifiedContentsFiles': True
    },
    'present.txt':{
        'duplicateFiles': False,
        'movedFiles': False,
        'newUnseenFiles': False,
        'modifiedFiles': False
    },
    'foxtrot\\newDupPair_1.txt': {
        'modifiedFiles': False
    },
    'alpha\\bravo\\newDupPair_2.txt': {
        'modifiedFiles': False
    }
}