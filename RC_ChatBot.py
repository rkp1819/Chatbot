import sqlite3
import json
from datetime import datetime
import time
##import wikipedia

timeframe = '2009-05'
sql_transaction = []
start_row = 0


connection = sqlite3.connect('{}.db'.format(timeframe))
c = connection.cursor()

def create_table():
    c.execute("CREATE TABLE IF NOT EXISTS parent_reply(parent_id TEXT PRIMARY KEY, comment_id TEXT UNIQUE, parent TEXT, comment TEXT, subreddit TEXT, unix INT, score INT)")


def transaction_bldr(sql):
    global sql_transaction
    sql_transaction.append(sql)
    if len(sql_transaction) > 10000:
        c.execute('BEGIN TRANSACTION')
        for s in sql_transaction:
            try:
                c.execute(s)
            except:
                pass
        connection.commit()
        sql_transaction = []

def sql_insert_replace_comment(commentid,parentid,parent,comment,subreddit,time,score):
    try:
        sql = """UPDATE parent_reply SET parent_id = ?, comment_id = ?, parent = ?, comment = ?, subreddit = ?, unix = ?, score = ? WHERE parent_id =?;""".format(parentid, commentid, parent, comment, subreddit, int(time), score, parentid)
        transaction_bldr(sql)
    except Exception as e:
        print('s0 insertion',str(e))

def sql_insert_has_parent(commentid,parentid,parent,comment,subreddit,time,score):
    try:
        sql = """INSERT INTO parent_reply (parent_id, comment_id, parent, comment, subreddit, unix, score) VALUES ("{}","{}","{}","{}","{}",{},{});""".format(parentid, commentid, parent, comment, subreddit, int(time), score)
        transaction_bldr(sql)
    except Exception as e:
        print('s0 insertion',str(e))

def sql_insert_no_parent(commentid,parentid,comment,subreddit,time,score):
    try:
        sql = """INSERT INTO parent_reply (parent_id, comment_id, comment, subreddit, unix, score) VALUES ("{}","{}","{}","{}",{},{});""".format(parentid, commentid, comment, subreddit, int(time), score)
        transaction_bldr(sql)
    except Exception as e:
        print('s0 insertion',str(e))

def acceptable(data):
    if len(data.split(' ')) > 1000 or len(data) < 1:
        return False
    elif len(data) > 32000:
        return False
    elif data == '[deleted]':
        return False
    elif data == '[removed]':
        return False
    else:
        return True

def find_parent(pid):
    try:
        sql = "SELECT comment FROM parent_reply WHERE comment_id = '{}' LIMIT 1".format(pid)
        c.execute(sql)
        result = c.fetchone()
        if result != None:
            return result[0]
        else: return False
    except Exception as e:
        #print(str(e))
        return False

def find_existing_score(pid):
    try:
        sql = "SELECT score FROM parent_reply WHERE parent_id = '{}' LIMIT 1".format(pid)
        c.execute(sql)
        result = c.fetchone()
        if result != None:
            return result[0]
        else: return False
    except Exception as e:
        #print(str(e))
        return False

def create_database():
    create_table()
    row_counter = 0
    paired_rows = 0
    
    with open('./RC_{}'.format(timeframe), buffering=1000) as f:
        for row in f:
            row_counter += 1

            if row_counter > start_row:
                try:
                    row = json.loads(row)
                    parent_id = row['parent_id'].split('_')[1]
                    body = row['body']
                    created_utc = row['created_utc']
                    score = row['score']
                    
                    comment_id = row['id']
                    
                    subreddit = row['subreddit']
                    parent_data = find_parent(parent_id)
                    
                    existing_comment_score = find_existing_score(parent_id)
                    if existing_comment_score:
                        if score > existing_comment_score:
                            if acceptable(body):
                                sql_insert_replace_comment(comment_id,parent_id,parent_data,body,subreddit,created_utc,score)
                                
                    else:
                        if acceptable(body):
                            if parent_data:
                                if score >= 1:
                                    sql_insert_has_parent(comment_id,parent_id,parent_data,body,subreddit,created_utc,score)
                                    paired_rows += 1
                            else:
                                sql_insert_no_parent(comment_id,parent_id,body,subreddit,created_utc,score)
                except Exception as e:
                    print(str(e))
                            
            if row_counter % 100000 == 0:
                print('Total Rows Read: {}, Paired Rows: {}, Time: {}'.format(row_counter, paired_rows, str(datetime.now())))


        print("Cleaning up!")
        sql = "DELETE FROM parent_reply WHERE parent IS NULL"
        c.execute(sql)
        connection.commit()
        c.execute("VACUUM")
        connection.commit()
    pass

def interact(input_data, subreddit):
    sql = """SELECT comment FROM parent_reply where  ABS( LENGTH(parent)-LENGTH("{0}") ) = 
            (SELECT MIN(ABS( LENGTH(parent)-LENGTH("{1}") )) FROM parent_reply WHERE LOWER(parent) LIKE "%{2}%")
            AND LOWER(parent) LIKE "%{3}%" ORDER BY score LIMIT 1""".format(input_data.lower(), input_data.lower(), input_data.lower(), input_data.lower())
    c.execute(sql)
    result = c.fetchone()
    if result != None:
        return result[0]
    else:
        print("wikipedia*************")
        return wikipedia.summary(input_data)

    
def clean_data(input_data):
    
    return input_data


if __name__ == '__main__':
    print("Enter 'quit()' to exit.")
    subreddit = input("Context: ")
    while(True):
        input_data = input("You:")
        if input_data == 'quit()':
            break
        output_data = interact(input_data, subreddit)
        print(output_data)
        












        
        



        
