import sqlite3

# table 1: indv_data
#Column Names: ['id', 'animal_id', 'year', 'idx', 'map_path', 'plt_aspect', 'min_long', 'max_long', 'min_lat', 'max_lat']

# Table 2: cluster_data
#Column Names: ['id', 'animal_id', 'year', 'idx', 'clustering_name', 'cluster_names', 'cluster_cmap']

# path
db_path = "database/individual_data.db"

# connect
connect = sqlite3.connect(db_path)
cursor = connect.cursor()

cursor.execute('SELECT * FROM cluster_data WHERE animal_id=?', ('5506092',))
#cursor.execute('DELETE FROM indv_data WHERE animal_id=?', ('5519114',))
result = cursor.fetchall()
for entry in result:
    print(entry)

# check if there are existing entries for this individual and this year
#cursor.execute("SELECT * FROM indv_data WHERE animal_id=? AND year=?", ('5519114', '2019'))
#result = cursor.fetchall()

#index = len(result) + 1 if result else 1
#print(index)

connect.commit()
connect.close()