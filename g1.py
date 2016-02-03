#!/usr/bin/env python


import sys
import re
import multiprocessing as mp

#__author__ = 'piniko'

'''

#on the psql shell
#create role pyuser login password 'pyuser';
#create database pydb owner pyuser;
#\l \dg
'''

import psycopg2
from psycopg2.extensions import AsIs
import argparse
import logging
from progressbar import AnimatedMarker, Bar, BouncingBar, Counter, ETA, FileTransferSpeed, FormatLabel, Percentage, ProgressBar, ReverseBar, RotatingMarker, SimpleProgress, Timer


parser = argparse.ArgumentParser(prog='psql_1000g_loader',usage='psql_1000g_loader [-t table_name -f file_input or -list file_input_list] [-ucsc_snpf file name -ucsc_snp table_name] (optional add a annotated ucsc_snp table from file ) [-dbname database_name -dbuser database_user -dbpass database_pass] [-a_ucsc chr table to be annotated by ucsc ] [-ensembl_variation_snpf file name -ensembl_variation_genename_snpf file name] (optional add a annotated ensembl tables from files) [-a_ensembl chr table to be annotated by ensemble ] [-sort_by_gene_and_pos ann_table] [-update_table_allel2peptide create all to peptide table] [-remove_dup_allele remove duplicate alleles from table] [-add_gene_peptide_string add gene_peptide_string fileds to table] [-create_uniq_pepstring_num create a table with unique number to each group of peptide strings ordered by descending] [-add_uniq_pepstring_num add unique pepstring number to specified table] [-export_sample_2file export 100 lines> of each table to file] [-export_fulldataset_2file export dataset in full to file name] [-s show all tables] [-add_meta add tables metadata]',description='Load annotated snp database & Create a 1000G sql table from all Chromosomes - using a connection to a postgresql DB.')

# dbname=pydb user=pyuser password=pyuser
# postgresql credentials
parser.add_argument("-dbname",required=True,help='name of psql database',metavar='DBNAME')
parser.add_argument("-dbuser",required=True,help='name of psql database user',metavar='DBUSER')
parser.add_argument("-dbpass",required=True,help='psql database user pass',metavar='DBPASS')


#1000g actions
parser.add_argument("-f",help='vcf file to load into psql database',metavar='VCF_FILE')
parser.add_argument("-t",help='destination vcf table on the psql database',metavar='PSQL_TABLE')
parser.add_argument("-list",help='file containing a list of files to load into psql database',metavar='VCF_FILE_LIST')

#UCSC's snp141CodingDbSnp annotated sr's actions: add amino acid annotation
parser.add_argument("-ucsc_snpf",help='a ucsc file to load into snp annotated table',metavar='UCSC_FILE')
parser.add_argument("-ucsc_snpt",help='destination table name for the snp annotated table',metavar='UCSC_PSQL_TABLE')

#add tables metadata : source , version of each table
parser.add_argument("-add_meta",help='add tables metadata : source , version of each table',action="store_true")


#ENSEMBL variation_  annotated sr's actions : combine gene_name and clinical attribute with rsid
parser.add_argument("-ensembl_variation_snpf",help='variation ensembl file to combine into ensembl snp annotated table',metavar='ENSEMBL_VARIATION_FILE')
parser.add_argument("-ensembl_variation_genename_snpf",help='variation genename ensembl file to combine into ensembl snp annotated table',metavar='ENSEMBL_VARIATION_GENENAME_FILE')

#add show tables option
parser.add_argument("-s", "--show_tables", help="show any existing tables",action="store_true")

#add ucsc annotation option with snp table input and chr table input
parser.add_argument("-a_ucsc",help='chr table to be annotated',metavar='ANN_TABLES_UCSC')

#sort specifiedn annotated table by chromStart - chrom position and create a new table
parser.add_argument("-sort",help='annotated table to be sorted by position',metavar='SORT_TABLES')

#sort specifiedn annotated table by chromStart - chrom position and create a new table
parser.add_argument("-sort_by_gene_and_pos",help='annotated table to be sorted by gene name and position',metavar='SORT_TABLES')

#add ensembl annotation option with snp table input and chr table input
parser.add_argument("-a_ensembl",help='chr table to be annotated',metavar='ANN_TABLES_ENSEMBL')

parser.add_argument("-update_table_allel2peptide",help=' create all to peptide table',metavar='UPDATE_ALLELE2PEP')

parser.add_argument("-remove_dup_allele",help='remove duplicate alleles from table',metavar='REMOVE_DUP_ALLELE')

parser.add_argument("-add_gene_peptide_string",help=' add gene_peptide_string fileds to table',metavar='ADD_GENE_PEPTIDE_STRING')

parser.add_argument("-create_uniq_pepstring_num",help=' create a table with unique number to each group of peptide strings ordered by descending',action="store_true")

parser.add_argument("-add_uniq_pepstring_num",help='add unique pepstring number to specified table',metavar='ADD_UNIQ_PEPSTRING_NUM')


parser.add_argument("-multi_core_num",help='use multiple cores number or \"max\"',metavar='MULTI_CORE_NUM')

parser.add_argument("-export_sample_2file",help='export sample to file name',metavar='export_sample_2file')

parser.add_argument("-export_fulldataset_2file",help='export dataset in full to file name',metavar='export_datasetfull_2file')

parser.add_argument("-o", "--overwrite_tables", help="overwrites any existing tables",action="store_true")
parser.add_argument("-v", "--verbose", help="increase output verbosity",action="store_true")
args=parser.parse_args()

#setup logging option
if args.verbose:
    logging.basicConfig(level=logging.DEBUG)




# DB vars :
dbname = args.dbname
dbuser = args.dbuser
dbpass = args.dbpass


#connection stuff
conn = psycopg2.connect("dbname="+dbname+" user="+dbuser+" password="+dbpass+" host=localhost")
cur = conn.cursor()



#setup ovwrwrite option
if args.overwrite_tables:
    overwrite_tables_is_set = True
    print("overwrite_tables_is_set")
else:
    overwrite_tables_is_set = False
    # print("overwrite_tables_is_NOT_set")

#counter col
column_limit = 20
column_limit_counter = 0
column_variable_counter = 0
#############################################################################################################################################

def insert_snp_table():


    print cur.mogrify("CREATE TABLE \"%s\" (\"bin\" smallint NOT NULL,\"chrom\" varchar(255) NOT NULL,\"chromStart\" int  NOT NULL,\"chromEnd\" int  NOT NULL, \"name\" text NOT NULL,\"transcript\" varchar(255) NOT NULL,\"frame\" varchar(255) NOT NULL,\"alleleCount\" int NOT NULL,\"funcCodes\" text NOT NULL,\"alleles\" text NOT NULL,\"codons\" text NOT NULL,\"peptides\" text NOT NULL)",(AsIs(snptable),))
    cur.execute("CREATE TABLE \"%s\" (\"bin\" smallint NOT NULL,\"chrom\" varchar(255) NOT NULL,\"chromStart\" int  NOT NULL,\"chromEnd\" int  NOT NULL, \"name\" text NOT NULL,\"transcript\" varchar(255) NOT NULL,\"frame\" varchar(255) NOT NULL,\"alleleCount\" int NOT NULL,\"funcCodes\" text NOT NULL,\"alleles\" text NOT NULL,\"codons\" text NOT NULL,\"peptides\" text NOT NULL)",(AsIs(snptable),))
    print cur.mogrify("COPY \"%s\" FROM \'%s\'",(AsIs(snptable),AsIs(snpfile),))
    cur.copy_from(fsnpfile, snptable)
    print cur.mogrify("CREATE TABLE %s AS SELECT * FROM \"%s\" WHERE frame NOT LIKE \"n/a\"",(AsIs(snptablena),AsIs(snptable),))
    cur.execute("CREATE TABLE %s AS SELECT * FROM \"%s\" WHERE frame NOT LIKE \'n/a\'",(AsIs(snptablena),AsIs(snptable),))
    print  cur.mogrify("CREATE TABLE %s AS SELECT * FROM %s WITH NO DATA",(AsIs(snptablenasma),AsIs(snptablena),))
    cur.execute("CREATE TABLE %s AS SELECT * FROM %s WITH NO DATA",(AsIs(snptablenasma),AsIs(snptablena),))
    print  cur.mogrify("ALTER TABLE %s "
                       "UMN peptide1 char(1), add column peptide2 char(2), add column peptide3 char(3)",(AsIs(snptablenasma),))
    cur.execute("ALTER TABLE %s ADD COLUMN peptide1 char(1), add column peptide2 char(2), add column peptide3 char(3)",(AsIs(snptablenasma),))
    print  cur.mogrify("INSERT INTO %s SELECT * FROM ( SELECT * , SUBSTR(peptides,1 , 1) AS peptide1 , SUBSTR(peptides,3 , 1) AS peptide2 , SUBSTR(peptides,5 , 1) AS peptide3 FROM %s ) AS ptt WHERE (peptide1!=peptide2) OR (peptide1!=peptide3) OR (peptide2!=peptide3)",(AsIs(snptablenasma),AsIs(snptablena),))
    cur.execute("INSERT INTO %s SELECT * FROM ( SELECT * , SUBSTR(peptides,1 , 1) AS peptide1 , SUBSTR(peptides,3 , 1) AS peptide2 , SUBSTR(peptides,5 , 1) AS peptide3 FROM %s ) AS ptt WHERE (peptide1!=peptide2) OR (peptide1!=peptide3) OR (peptide2!=peptide3)",(AsIs(snptablenasma),AsIs(snptablena),))
    print  cur.mogrify("CREATE TABLE %s AS SELECT * FROM %s ORDER BY codons",(AsIs(snptable_s_c),AsIs(snptablenasma),))
    cur.execute("CREATE TABLE %s AS SELECT * FROM %s ORDER BY codons",(AsIs(snptable_s_c),AsIs(snptablenasma),))
    print  cur.mogrify("CREATE TABLE %s AS SELECT * FROM %s ORDER BY \"chromStart\"",(AsIs(snptable_s_ch_filtered_final),AsIs(snptable_s_c),))
    cur.execute("CREATE TABLE %s AS SELECT * FROM %s ORDER BY \"chromStart\"",(AsIs(snptable_s_ch_filtered_final),AsIs(snptable_s_c),))
    conn.commit()


def cleanup_err_tables():

    del_tables_list = (snptable,snptablena,snptablenasma,snptable_s_c,snptable_s_ch_filtered_final)
    for table in del_tables_list:
        if check_table_exists(table):
            print(cur.mogrify("drop table "+table+";"))
            cur.execute("drop table "+table+";")
            conn.commit()


    for table in table1000g_list:
        print("table to be deleted "+table)
        if check_table_exists(table):
            print(cur.mogrify("drop table "+table+";"))
            cur.execute("drop table "+table+";")
            conn.commit()

def cleanup_snp_tables():

    snp_del_tables = (snptable,snptablena,snptablenasma,snptable_s_c)
    for table in snp_del_tables:
        check_table_exists(table)
        print(cur.mogrify("drop table "+table+";"))
        cur.execute("drop table "+table+";")
        conn.commit()


def check_table_exists(table1):
    cur.execute("select * from information_schema.tables where table_name=\'%s\'",(AsIs(table1),))
    return bool(cur.fetchall())

def delete_table(table3):
    print(cur.mogrify("drop table "+table3+";"))
    cur.execute("drop table "+table3+";")
    conn.commit()

def check_empty_table(table2):
    cur.execute("select * from %s limit 1;" , (AsIs(table2),))
    return str(bool(cur.fetchall()))

def create_table(table4):

    ##delete if overwrite_tables_is_set is set here!
    print(cur.mogrify("create table "+table4+"();"))
    cur.execute("create table "+table4+"();")
    conn.commit()


def addcol (column_name):
   logging.debug(cur.mogrify("alter table "+table1000g+" add column %s text;", (AsIs(column_name),)))
   cur.execute("alter table "+table1000g+" add column %s text;", (AsIs(column_name),))
   conn.commit()


def load_1000g():

    global column_variable_counter
    global column_limit_counter
    #define progress bar object
    widgets = ['database upload -> '+table1000g+' :', Percentage(), ' ', Bar(marker=RotatingMarker()),' ', ETA(), ' ', FileTransferSpeed()]

    pbar = ProgressBar(widgets=widgets, maxval=10000000).start()

    with open(myfile) as f:

       # print "loading : "+table1000g+"...."
       ##latest change to file and remove readlines
       for line in pbar(f):
            logging.debug("whole line :"+line)
            # find columns row and set it as column names

            #skip if table is initialized with colums
    #       option to have all files in single table
    #         if not check_empty_table(table1000g):
            ##add tab

            if re.match("^#(?!#)",line):
                logging.debug("found1#!")
                col_words = line.split()
                col_counter = len(col_words)
                logging.debug("column list length")
                logging.debug(col_counter)

                for word in line.split():

                  #skip after 20 column

                  if column_limit_counter >= column_limit:
                    column_limit_counter=0
                    break
                  column_limit_counter+=1


                  if word.startswith('#'):
                    logging.debug(word.replace("#","")+"word"+str(col_counter))
                    wo = word.replace("#","")
                    addcol(wo)
                  else :
                    logging.debug(word+" word"+str(col_counter))
                    addcol(word)

            # first check the line length and compare to columns number
            #find and load variable lines
            if (not line.startswith('#')) and ("CNV" not in line):
                col_words2 = line.split()
                word_counter = len(col_words2)
                if word_counter == col_counter:
                    logging.debug("variables list length :")
                    logging.debug(word_counter)
                    logging.debug("column list length :")
                    logging.debug(col_counter)
                    linequoted = ""

                    for word in line.split():

                        #skip after 20 column
                        if column_variable_counter >= column_limit:
                            column_variable_counter=0
                            break

                        column_variable_counter+=1


                        wordquoted='\''+word+'\''','
                        logging.debug(wordquoted)
                        linequoted += wordquoted

                    logging.debug(linequoted)
                    insertline=linequoted[:-1]

                    insert_values(insertline)


def insert_values(line):
    logging.debug(cur.mogrify("insert into "+table1000g+" values (%s);", (AsIs(line),)))
    cur.execute("insert into "+table1000g+" values (%s);", (AsIs(line),))
    conn.commit()

def check_1000g_table():
    if check_table_exists(table1000g):

        print "Table "+table1000g+" exists !"

        ans = (raw_input("Are you sure you want to reset this table ? (yes/no)"))
        if ans == "yes":

            delete_table(table1000g)
            create_table(table1000g)

        elif ans == "no":

            global abort_1000g_table
            abort_1000g_table = "true"
        else:
            print "please answear yes or no ..."
            check_1000g_table()
    else:
        create_table(table1000g)

def check_overwrite_table(table8):

        if check_table_exists(table8):
            print "Table "+table8+" exists !"
            ans = (raw_input("Are you sure you want to reset this table ? (yes/no)"))
            if ans == "yes":

                delete_table(table8)
            elif ans == "no":

                pass

            else:
                print "please answear yes or no ..."
                check_overwrite_table()

def sort_annotated(anntable):

    sortedtable = args.sort+"sorted"

    cur.mogrify("create table %s as select * from %s order by \"chromStart\";",(AsIs(sortedtable),AsIs(anntable),))
    cur.execute("create table %s as select * from %s order by \"chromStart\";",(AsIs(sortedtable),AsIs(anntable),))
    conn.commit()

def sort_by_gene_and_pos(anntable2):

    sortedtable2 = args.sort_by_gene_and_pos+"sorted_by_gene_pos"
    cur.mogrify("create table %s as select * from %s order by \"chromStart\" , \"gene_name\" ;",(AsIs(sortedtable2),AsIs(anntable2),))
    cur.execute("create table %s as select * from %s order by \"chromStart\" , \"gene_name\" ;",(AsIs(sortedtable2),AsIs(anntable2),))
    conn.commit()

def check_snp_table():

        if check_table_exists(snptable_s_ch_filtered_final):
            print "Table "+snptable_s_ch_filtered_final+" exists !"
            ans = (raw_input("Are you sure you want to reset this table ? (yes/no)"))
            if ans == "yes":

                delete_table(snptable_s_ch_filtered_final)
            elif ans == "no":

                global abort_snp_table
                abort_snp_table = "true"
            else:
                print "please answear yes or no ..."
                check_snp_table()


# def join_chr_with_anno_snp(chrtable):
#join with ensemble snp
def join_chr_with_anno_ucsc_snp():

    cur.execute("SELECT tablename FROM pg_catalog.pg_tables where tableowner='pyuser' and tablename like '%filtered_final'")
    snpname=str(cur.fetchall())
    if not snpname:
        print "no snp annotated table present"
        sys.exit()
    else:

        annsnp = snpname[3:-4]
        annsnptemp = annsnp+"temp"

    chr2bann = args.a_ucsc+"ann"

    #check overwrite or errstop

    check_overwrite_table(chr2bann)
    # check_overwrite_table(annsnptemp)

    if not check_table_exists(annsnptemp):

        #first copy the snp table without the chrom column

        print(cur.mogrify("create table %s as select * from %s ",(AsIs(annsnptemp),AsIs(annsnp))))
        cur.execute("create table %s as select * from %s ",(AsIs(annsnptemp),AsIs(annsnp)))
        conn.commit()

        print(cur.mogrify("alter table %s drop column chrom", (AsIs(annsnptemp),)))
        cur.execute("alter table %s drop column chrom", (AsIs(annsnptemp),))
        conn.commit()

    # then inner join the annsnp table with the chrtable
    print(cur.mogrify("CREATE TABLE %s AS SELECT * FROM %s inner join %s on (%s.name = %s.id)",(AsIs(chr2bann),AsIs(annsnptemp),AsIs(args.a_ucsc),AsIs(annsnptemp),AsIs(args.a_ucsc),)))
    cur.execute("CREATE TABLE %s AS SELECT * FROM %s inner join %s on (%s.name = %s.id)",(AsIs(chr2bann),AsIs(annsnptemp),AsIs(args.a_ucsc),AsIs(annsnptemp),AsIs(args.a_ucsc),))
    conn.commit()

    # #clean up temp table
#    print(cur.mogrify("drop table if exists %s",(AsIs(annsnptemp),)))
 #   cur.execute("drop table if exists %s",(AsIs(annsnptemp),))
  #  conn.commit()

#load 2 tables from ensembl , one with gana_name and the other with clinical segnificanse, add them together
def add_ann_ensembl():

    e1 = "ensembl_variation"
    e2 = "ensembl_variation_genename"

    if not check_table_exists(e1):
        print cur.mogrify("CREATE TABLE ensembl_variation (\"variation_id\" int ,\"source_id\" int ,\"rs_name\" text ,\"validation_status\" text ,\"ancestral_allele\" text ,\"flipped\" boolean ,\"class_attrib_id\" int ,\"somatic\" boolean ,\"minor_allele\" text ,\"minor_allele_freq\" real ,\"minor_allele_count\" int ,\"clinical_significance\" text , \"evidence\" text)")
        cur.execute("CREATE TABLE ensembl_variation (\"variation_id\" int ,\"source_id\" int ,\"rs_name\" text ,\"validation_status\" text ,\"ancestral_allele\" text ,\"flipped\" boolean ,\"class_attrib_id\" int ,\"somatic\" boolean ,\"minor_allele\" text ,\"minor_allele_freq\" real ,\"minor_allele_count\" int ,\"clinical_significance\" text , \"evidence\" text)")
        conn.commit()


    if not check_table_exists(e2):
        print cur.mogrify("CREATE TABLE ensembl_variation_genename (\"variation_id2\" int ,  \"gene_name\" text)")
        cur.execute("CREATE TABLE ensembl_variation_genename (\"variation_id2\" int ,  \"gene_name\" text)")
        conn.commit()

    #copy data to the tables

    print ("COPY ensembl_variation FROM "+args.ensembl_variation_snpf)
    cur.copy_from(ensembl_variation_file, "ensembl_variation")
    conn.commit()
    print ("COPY ensembl_variation FROM "+args.ensembl_variation_genename_snpf)
    cur.copy_from(ensembl_variation_genename_file, "ensembl_variation_genename")
    conn.commit()
    #join them to a new table : variation_genename_4ann

    print cur.mogrify("CREATE TABLE variation_genename_4ann AS SELECT * FROM ensembl_variation inner join ensembl_variation_genename on (ensembl_variation.variation_id = ensembl_variation_genename.variation_id2)")
    cur.execute("CREATE TABLE variation_genename_4ann AS SELECT * FROM ensembl_variation inner join ensembl_variation_genename on (ensembl_variation.variation_id = ensembl_variation_genename.variation_id2)")
    conn.commit()

    print cur.mogrify("alter table variation_genename_4ann drop column variation_id2")
    print cur.execute("alter table variation_genename_4ann drop column variation_id2")
    conn.commit()


#add tables meta data , this is a static table
def add_meta():
    if not check_table_exists("tables_meta"):
        print (cur.mogrify("create table tables_meta (\"source\" text, \"Genome\" text, \"Reference_Consortium_Human_Reference\" text, \"table_name\" text, \"schema_link\" text, \"table link\" text, \"documentation_link\" text, \"date_downloaded\" text) "))
        cur.execute("create table tables_meta (\"source\" text, \"Genome\" text, \"Reference_Consortium_Human_Reference\" text, \"table_name\" text, \"schema_link\" text, \"table link\" text, \"documentation_link\" text, \"date_downloaded\" text) ")
        conn.commit()
        print ("insert into tables_meta values(\'ucsc\', \'GRCh37\', \'snp141CodingDbSnp\', \'http://hgdownload.cse.ucsc.edu/goldenpath/hg19/database/snp141CodingDbSnp.sql\', \'http://hgdownload.cse.ucsc.edu/goldenpath/hg19/database/snp141CodingDbSnp.txt.gz\', \'http://hgdownload.cse.ucsc.edu/goldenpath/hg19/database/\', \'10.2015\')")
        cur.execute("insert into tables_meta values(\'ucsc\', \'GRCh37\', \'snp141CodingDbSnp\', \'http://hgdownload.cse.ucsc.edu/goldenpath/hg19/database/snp141CodingDbSnp.sql\', \'http://hgdownload.cse.ucsc.edu/goldenpath/hg19/database/snp141CodingDbSnp.txt.gz\', \'http://hgdownload.cse.ucsc.edu/goldenpath/hg19/database/\', \'10.2015\')")
        conn.commit()
        print("insert into tables_meta values(\'ensembl\', \'GRCh37\', \'variation,  variation_genename\', \'ftp://ftp.ensembl.org/pub/release-75/mysql/homo_sapiens_variation_75_37/homo_sapiens_variation_75_37.sql.gz\', \'ftp://ftp.ensembl.org/pub/release-75/mysql/homo_sapiens_variation_75_37/variation.txt.gz,  ftp://ftp.ensembl.org/pub/release-75/mysql/homo_sapiens_variation_75_37/variation_genename.txt.gz\', \'http://grch37.ensembl.org/info/docs/api/variation/variation_schema.html#variation\', \'8.2015\')")
        cur.execute("insert into tables_meta values(\'ensembl\', \'GRCh37\', \'variation,  variation_genename\', \'ftp://ftp.ensembl.org/pub/release-75/mysql/homo_sapiens_variation_75_37/homo_sapiens_variation_75_37.sql.gz\', \'ftp://ftp.ensembl.org/pub/release-75/mysql/homo_sapiens_variation_75_37/variation.txt.gz,  ftp://ftp.ensembl.org/pub/release-75/mysql/homo_sapiens_variation_75_37/variation_genename.txt.gz\', \'http://grch37.ensembl.org/info/docs/api/variation/variation_schema.html#variation\', \'8.2015\')")
        conn.commit()
        print("insert into tables_meta values(\'1000genomes\', \'GRCh37\', \'ALL.chrXX.phase3\', \'ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/release/20130502/\', \'ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/release/20130502/\', \'http://www.1000genomes.org/faq\', \'7.2015\')")
        cur.execute("insert into tables_meta values(\'1000genomes\', \'GRCh37\', \'ALL.chrXX.phase3\', \'ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/release/20130502/\', \'ftp://ftp-trace.ncbi.nih.gov/1000genomes/ftp/release/20130502/\', \'http://www.1000genomes.org/faq\', \'7.2015\')")
        conn.commit()


def join_chr_with_anno_ensembl_snp():
    if not check_table_exists("variation_genename_4ann"):
        print "no snp annotated table present"
        sys.exit()

    #new annotation table to be created
    chr2bann_ensembl = args.a_ensembl+"2"

    check_overwrite_table(chr2bann_ensembl)

    #  inner join the ensembl table with the chranntable
    print(cur.mogrify("CREATE TABLE %s AS SELECT * FROM %s inner join variation_genename_4ann on (%s.name = variation_genename_4ann.rs_name)",(AsIs(chr2bann_ensembl),AsIs(args.a_ensembl),AsIs(args.a_ensembl),)))

    cur.execute("CREATE TABLE %s AS SELECT * FROM %s inner join variation_genename_4ann on (%s.name = variation_genename_4ann.rs_name)",(AsIs(chr2bann_ensembl),AsIs(args.a_ensembl),AsIs(args.a_ensembl),))
    conn.commit()


def multifunc(arg):
    print arg, "print"
    return arg,"return"

def multiquery(num):

    conn2 = psycopg2.connect("dbname="+dbname+" user="+dbuser+" password="+dbpass+" host=localhost")
    conn2.set_session(autocommit=True)
    cur2 = conn2.cursor()


    cur2.execute("create table bla%s();", (AsIs(num),))
    # cur2.execute("drop table bla%s;", (AsIs(num),))
    # cur2.mogrify("drop table bla%s;", (AsIs(num),))
    cur2.mogrify("create table bla%s();", (AsIs(num),))
    print str(cur.fetchall())



def isInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False

def query2list():
    global querylist
    querylist = []
    va2all_query = cur.fetchall()
    for i3 in va2all_query:
        for index,i2 in enumerate(i3):

            if index == len(i3) - 1:
                word12 = ''.join(i2)
                # print(word12)
            querylist.extend([word12])
            # print querylist
    return querylist




# initialise variables
table_exists = ""
table1000g = ""
Fileinput = ""
file_list = ""
myfile = ""
snptable = ""
snptablena = ""
snptablenasma = ""
snptable_s_c = ""
snptable_s_ch_filtered_final = ""
snpfile = ""
fsnpfile = ""

abort_snp_table = ""
abort_1000g_table = ""

table1000g_list = []

# check what the user wanted to do :
# load a 1000g taable
# load a snp annotated table
# both
#start##################################################################################################################

#optional clean / overwrite tables

# if overwrite_tables_is_set:
#     cleanup_err_tables()


try:


    if args.ucsc_snpt and args.ucsc_snpf:
        #snp anno. vars
        snptable = args.ucsc_snpt
        snptablena = args.ucsc_snpt+"na"
        snptablenasma = args.ucsc_snpt+"sma"
        snptable_s_c = args.ucsc_snpt+"_s_c"
        snptable_s_ch_filtered_final = args.ucsc_snpt+"_s_ch_filtered_final"
        snpfile = args.ucsc_snpf
        fsnpfile = open(snpfile)

        #check if exists
        check_snp_table()
        if abort_snp_table == "true":
            pass
        else:
            #load snp annot
            insert_snp_table()
            # do clean up
            cleanup_snp_tables()

    elif (not args.ucsc_snpt and args.ucsc_snpf) or (not args.ucsc_snpf and args.ucsc_snpt):
        print "argument missing !"
        parser.print_help()
        sys.exit()


# list path vs file path

    if args.list:


    #if the user gave a list containing 1000g file list
        if args.list and args.t:
             with open(args.list) as file_list:
                for file_list_line in file_list.readlines():

                    Fileinput = file_list_line.rstrip()
                    # 1000g vars
                    ch_name = re.search('chr.[0-9]|chr.', str(file_list_line))

                    if not ch_name:
                        print "\n ERROR : problem : wrong file name for 1000g file \n please use original vcf file names (containing \"chr\" string)"
                        print "error in file name :"+str(file_list_line)
                        sys.exit()

                    table1000g = args.t+ch_name.group(0)
                    #add to list for cleanup
                    table1000g_list.append(table1000g)
                    print("tablename = "+table1000g)
                    #set the 1000gfile
                    myfile = str(Fileinput)
                    #check if exists
                    #if overwrite is set delete and recreate table
                    if overwrite_tables_is_set == True:
                        if  check_table_exists(table1000g):
                            delete_table(table1000g)
                        create_table(table1000g)
                        load_1000g()
                    else:
                        check_1000g_table()
                        if abort_1000g_table == "true":
                            abort_1000g_table = "false"
                            pass
                        else:
                            #load 1000g table
                            load_1000g()
        elif (not args.t and args.list) or (not args.list and args.t):
            print "argument missing !"
            parser.print_help()
            sys.exit()

    elif not args.list:
#file not list
    #if the user gave a single 1000g file list

        if args.t and args.f:

            # 1000g vars
            ch_name = re.search('chr.[0-9]|chr.', args.f)
            if not ch_name:
                print "\n ERROR : problem : wrong file name for 1000g file \n please use original vcf file names (containing \"chr\" string)"
                print "error in file name :"+str(args.f)
                sys.exit()

            Fileinput = args.f
            table1000g = args.t+ch_name.group(0).lower()
            #set the 1000gfile
            myfile = str(Fileinput)
            #check if exists
            #if overwrite is set delete and recreate table
            if overwrite_tables_is_set == True:
                delete_table(table1000g)
                create_table(table1000g)
            else:
                check_1000g_table()
                if abort_1000g_table == "true":
                    pass
                else:
                    #load 1000g table
                    load_1000g()

        elif (not args.t and args.f) or (not args.f and args.t):
            print "argument missing !"
            parser.print_help()
            sys.exit()

    #show tables option
    if args.show_tables:
        # cur.execute("SELECT tablename FROM pg_catalog.pg_tables where tableowner='%s'",(AsIs(dbuser)),)
        cur.execute("SELECT tablename FROM pg_catalog.pg_tables where tableowner='"+dbuser+"'")
        print str(cur.fetchall())


    if args.a_ucsc:
        join_chr_with_anno_ucsc_snp()

    if args.sort:
        sort_annotated(args.sort)

    if args.sort_by_gene_and_pos:
        sort_by_gene_and_pos(args.sort_by_gene_and_pos)

    if args.add_meta:
        add_meta()

#ensembl tables block
    if args.ensembl_variation_snpf and args.ensembl_variation_genename_snpf:
        #ensembl snp anno. vars
        ensembl_variation_file = open(args.ensembl_variation_snpf)
        ensembl_variation_genename_file = open(args.ensembl_variation_genename_snpf)

        enslist = ["ensembl_variation","ensembl_variation_genename","variation_genename_4ann"]

        for enstable in enslist:
            if check_table_exists(enstable):
                evans = raw_input("Are you sure you want to reset "+enstable+" table ? (yes/no)")
                if evans == "yes":
                    print "reseting "+enstable+" table"
                    delete_table(enstable)

        #enslist loop
        add_ann_ensembl()


    elif (not args.ensembl_variation_genename_snpf and args.ensembl_variation_snpf) or (not args.ensembl_variation_snpf and args.ensembl_variation_genename_snpf):
        print "argument missing !"
        parser.print_help()
        sys.exit()

# add ensembl annotation to chr
    if args.a_ensembl:
        join_chr_with_anno_ensembl_snp()
#old export table:
#export to file sample of 100 from each table
    # if args.export_sample_2file:
    #    with open (args.export_sample_2file, "a") as export_file:
    #
    #        cur.execute("select tablename from pg_tables where tableowner='pyuser';")
    #        for i in cur.fetchall():
    #            sample_table = ''.join(i)
    #            if sample_table.endswith("sorted_by_gene_pos"):
    #                print "\n"
    #                print "table : ", sample_table
    #                print "\n"
    #                #  select * from g1000chr1ann2sorted_by_gene_pos where false
    #                cur.execute("select column_name from information_schema.columns where table_name = '%s';;",(AsIs(sample_table),))
    #                # print(cur.fetchall())
    #
    #                print(re.sub('(\,\))|(\()|(\[)|(\])|(\))','',str(cur.fetchall())))
    #                # print "\n"
    #                # export_file.write(cur.fetchall())
    #                cur.execute("select * from %s limit 100;",(AsIs(sample_table),))
    #                # print(cur.fetchall())
    #                for i2 in cur.fetchall():
    #                    print "\n"
    #                    print(re.sub('(\,\))|(\()|(\[)|(\])|(\))','',str(i2)))
    #                # export_file.write(cur.fetchall())

    #export to file sample of 100 from each table
    if args.export_sample_2file:
       firstline = True
       with open(args.export_sample_2file,"a") as export_file:

           cur.execute("select tablename from pg_tables where tableowner='pyuser';")
           for i in cur.fetchall():
               sample_table = ''.join(i)
               if sample_table.endswith("strnum"):

                    if firstline == True:

                        cur.execute("select column_name from information_schema.columns where table_name = '%s';",(AsIs(sample_table),))
                        row12 = cur.fetchall()
                        for index,i2 in enumerate(row12):
                            if index == len(row12) - 1 :
                                word12 = ''.join(i2)
                                export_file.write(word12)
                            else:
                                word12 = ''.join(i2) + ","
                                export_file.write(word12)
                        export_file.write("\n")

                        firstline = False

                    cur.execute("select * from %s limit 100;",(AsIs(sample_table),))
                    row12 = cur.fetchall()
                    for i3 in row12:
                        for index,i2 in enumerate(i3):

                            if index == len(i3) - 1:
                                word12 = ''.join(i2)
                                export_file.write(word12)
                            else:
                                if str(i2).isspace():
                                    i2 = re.sub('\s+','',str(i2))
                                    word12 = str(i2) + ","
                                    export_file.write(word12)
                                elif str(i2).isdigit():
                                    i2 = str(i2).strip()
                                    word12 = "\""+str(i2)+"\""
                                    word12 = str(i2) + ","
                                    export_file.write(word12)
                                elif not str(i2).isdigit():
                                    if str(i2) == "None":
                                        i2 = " "
                                    i2 = str(i2).strip()
                                    i2 = re.sub(',$','',i2)
                                    i2= re.sub(',',';',i2)
                                    word12 = str(i2) + "\',"
                                    export_file.write("\'"+word12)
                        export_file.write("\n")



##new full export

    #export to file sample of 100 from each table
    if args.export_fulldataset_2file:
       firstline = True
       with open(args.export_fulldataset_2file,"a") as export_file:

           cur.execute("select tablename from pg_tables where tableowner='pyuser';")
           for i in cur.fetchall():
               sample_table = ''.join(i)
               if sample_table.endswith("strnum"):

                    print "now exporting :   "+sample_table

                    if firstline == True:

                        cur.execute("select column_name from information_schema.columns where table_name = '%s';",(AsIs(sample_table),))
                        row12 = cur.fetchall()
                        for index,i2 in enumerate(row12):
                            if index == len(row12) - 1 :
                                word12 = ''.join(i2)
                                export_file.write(word12)
                            else:
                                word12 = ''.join(i2) + ","
                                export_file.write(word12)
                        export_file.write("\n")

                        firstline = False

                    cur.execute("select * from %s;",(AsIs(sample_table),))
                    row12 = cur.fetchall()
                    for i3 in row12:
                        for index,i2 in enumerate(i3):

                            if index == len(i3) - 1:
                                word12 = ''.join(i2)
                                export_file.write(word12)
                            else:
                                if str(i2).isspace():
                                    i2 = re.sub('\s+','',str(i2))
                                    word12 = str(i2) + ","
                                    export_file.write(word12)
                                elif str(i2).isdigit():
                                    i2 = str(i2).strip()
                                    word12 = "\""+str(i2)+"\""
                                    word12 = str(i2) + ","
                                    export_file.write(word12)
                                elif not str(i2).isdigit():
                                    if str(i2) == "None":
                                        i2 = " "
                                    i2 = str(i2).strip()
                                    i2 = re.sub(',$','',i2)
                                    i2= re.sub(',',';',i2)
                                    word12 = str(i2) + "\',"
                                    export_file.write("\'"+word12)
                        export_file.write("\n")



# add variation peptide scetion :
#
    if args.update_table_allel2peptide:
        var2all_table = args.update_table_allel2peptide + "al2p"
        check_overwrite_table(var2all_table)
        # if not check_table_exists(var2all_table):

        print(cur.mogrify("create table %s as select * from %s ",(AsIs(var2all_table),AsIs(args.update_table_allel2peptide),)))
        cur.execute("create table %s as select * from %s ",(AsIs(var2all_table),AsIs(args.update_table_allel2peptide),))
        conn.commit()

        hg = "hg%"

        print(cur.mogrify("select column_name from information_schema.columns where table_name = '%s' and column_name like \'%s\';",(AsIs(var2all_table),AsIs(hg),)))
        cur.execute("select column_name from information_schema.columns where table_name = '%s' and column_name like \'%s\';",(AsIs(var2all_table),AsIs(hg),))

        for hg2 in query2list():

            print(cur.mogrify("update %s set %s = (case when (%s='0') then  peptide1 when (%s='0|0') then  peptide1||peptide1 when (%s='0|1') then peptide1||peptide2 when (%s='0|2') then  peptide1||peptide3 when (%s='1') then  peptide2 when (%s='1|0') then  peptide2||peptide1 when (%s='1|1') then  peptide2||peptide2 when (%s='1|2') then  peptide2||peptide3 when (%s='2') then  peptide3 when (%s='2|0') then  peptide3||peptide1 when (%s='2|1') then  peptide3||peptide2 when (%s='2|2') then  peptide3||peptide3 end)",(AsIs(var2all_table),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),)))
            cur.execute("update %s set %s = (case when (%s='0') then  peptide1 when (%s='0|0') then  peptide1||peptide1 when (%s='0|1') then peptide1||peptide2 when (%s='0|2') then  peptide1||peptide3 when (%s='1') then  peptide2 when (%s='1|0') then  peptide2||peptide1 when (%s='1|1') then  peptide2||peptide2 when (%s='1|2') then  peptide2||peptide3 when (%s='2') then  peptide3 when (%s='2|0') then  peptide3||peptide1 when (%s='2|1') then  peptide3||peptide2 when (%s='2|2') then  peptide3||peptide3 end)",(AsIs(var2all_table),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),AsIs(hg2),))
            conn.commit()
            print hg2

#create new tables without duplicate alleles
    if args.remove_dup_allele:

        var_nodup_table = args.remove_dup_allele+ "nodup"
        check_overwrite_table(var_nodup_table)


        print(cur.mogrify("create table %s as select * from %s WHERE peptide1!=peptide2 and peptide1!=peptide3 and peptide2!=peptide3",(AsIs(var_nodup_table),AsIs(args.remove_dup_allele),)))
        cur.execute("create table %s as select * from %s WHERE peptide1!=peptide2 and peptide1!=peptide3 and peptide2!=peptide3",(AsIs(var_nodup_table),AsIs(args.remove_dup_allele),))
        conn.commit()


    if args.add_gene_peptide_string:

        varpepstr_table = args.add_gene_peptide_string + "pepstr"
        varpepstr_temp_table = args.add_gene_peptide_string + "temp"

        check_overwrite_table(varpepstr_table)



#get a list of patients

        hg = "hg%"

        print(cur.mogrify("select column_name from information_schema.columns where table_name = '%s' and column_name like \'%s\';",(AsIs(args.add_gene_peptide_string),AsIs(hg),)))
        cur.execute("select column_name from information_schema.columns where table_name = '%s' and column_name like \'%s\';",(AsIs(args.add_gene_peptide_string),AsIs(hg),))

#load ersults into list :

        query2list()
#create table with gene and pep list :

        if not check_table_exists(varpepstr_temp_table):

            print(cur.mogrify("create table %s as select gene_name as gene,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string from %s group by gene_name;",(AsIs(varpepstr_temp_table),AsIs(querylist[0]),AsIs(querylist[0]),AsIs(querylist[0]),AsIs(querylist[1]),AsIs(querylist[1]),AsIs(querylist[1]),AsIs(querylist[2]),AsIs(querylist[2]),AsIs(querylist[2]),AsIs(querylist[3]),AsIs(querylist[3]),AsIs(querylist[3]),AsIs(querylist[4]),AsIs(querylist[4]),AsIs(querylist[4]),AsIs(querylist[5]),AsIs(querylist[5]),AsIs(querylist[5]),AsIs(querylist[6]),AsIs(querylist[6]),AsIs(querylist[6]),AsIs(querylist[7]),AsIs(querylist[7]),AsIs(querylist[7]),AsIs(querylist[8]),AsIs(querylist[8]),AsIs(querylist[8]),AsIs(querylist[9]),AsIs(querylist[9]),AsIs(querylist[9]),AsIs(querylist[10]),AsIs(querylist[10]),AsIs(querylist[10]),AsIs(args.add_gene_peptide_string),)))
            cur.execute("create table %s as select gene_name as gene,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string,string_agg(%s,'' order by %s) as %speptide_string from %s group by gene_name;",(AsIs(varpepstr_temp_table),AsIs(querylist[0]),AsIs(querylist[0]),AsIs(querylist[0]),AsIs(querylist[1]),AsIs(querylist[1]),AsIs(querylist[1]),AsIs(querylist[2]),AsIs(querylist[2]),AsIs(querylist[2]),AsIs(querylist[3]),AsIs(querylist[3]),AsIs(querylist[3]),AsIs(querylist[4]),AsIs(querylist[4]),AsIs(querylist[4]),AsIs(querylist[5]),AsIs(querylist[5]),AsIs(querylist[5]),AsIs(querylist[6]),AsIs(querylist[6]),AsIs(querylist[6]),AsIs(querylist[7]),AsIs(querylist[7]),AsIs(querylist[7]),AsIs(querylist[8]),AsIs(querylist[8]),AsIs(querylist[8]),AsIs(querylist[9]),AsIs(querylist[9]),AsIs(querylist[9]),AsIs(querylist[10]),AsIs(querylist[10]),AsIs(querylist[10]),AsIs(args.add_gene_peptide_string),))

        conn.commit()


#join peplistst table into new table create new table

        # create table test1 as select * from g1000chr1ann2sorted_by_gene_posal2p inner join g1000chr1ann2sorted_by_gene_posal2ptemp on (g1000chr1ann2sorted_by_gene_posal2p.gene_name = g1000chr1ann2sorted_by_gene_posal2ptemp.gene);

        print(cur.mogrify("create table %s as select * from %s inner join %s on (%s.gene_name = %s.gene)",(AsIs(varpepstr_table),AsIs(args.add_gene_peptide_string),AsIs(varpepstr_temp_table),AsIs(args.add_gene_peptide_string),AsIs(varpepstr_temp_table),)))
        cur.execute("create table %s as select * from %s inner join %s on (%s.gene_name = %s.gene)",(AsIs(varpepstr_table),AsIs(args.add_gene_peptide_string),AsIs(varpepstr_temp_table),AsIs(args.add_gene_peptide_string),AsIs(varpepstr_temp_table),))
        conn.commit()

    #cleap up temp table

        print(cur.mogrify("drop table %s",(AsIs(varpepstr_temp_table),)))
        cur.execute("drop table %s",(AsIs(varpepstr_temp_table),))
        conn.commit()


    if args.create_uniq_pepstring_num:

        varallchpepstr = "allchpepstr"
        check_overwrite_table(varallchpepstr)

        pepvar ="%str"

        varallchpepstrcount="allchpepstrcount"
        check_overwrite_table(varallchpepstrcount)


        varallchpepstrcountsum="allchpepstrcountsum"
        check_overwrite_table(varallchpepstrcountsum)

 #create one big table from latets
        cur.execute("select table_name from information_schema.tables where table_name like \'%s\'",(AsIs(pepvar),))

        query2list()


        print(cur.mogrify("create table allchpepstr as select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s",(AsIs(querylist[0]), AsIs(querylist[1]), AsIs(querylist[2]), AsIs(querylist[3]), AsIs(querylist[4]), AsIs(querylist[5]), AsIs(querylist[6]), AsIs(querylist[7]), AsIs(querylist[8]), AsIs(querylist[9]), AsIs(querylist[10]), AsIs(querylist[11]), AsIs(querylist[12]), AsIs(querylist[13]), AsIs(querylist[14]), AsIs(querylist[15]), AsIs(querylist[16]), AsIs(querylist[17]), AsIs(querylist[18]), AsIs(querylist[19]), AsIs(querylist[20]), AsIs(querylist[21]), AsIs(querylist[22]), AsIs(querylist[23]),)))


        cur.execute("create table allchpepstr as select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s union all select * from %s",(AsIs(querylist[0]), AsIs(querylist[1]), AsIs(querylist[2]), AsIs(querylist[3]), AsIs(querylist[4]), AsIs(querylist[5]), AsIs(querylist[6]), AsIs(querylist[7]), AsIs(querylist[8]), AsIs(querylist[9]), AsIs(querylist[10]), AsIs(querylist[11]), AsIs(querylist[12]), AsIs(querylist[13]), AsIs(querylist[14]), AsIs(querylist[15]), AsIs(querylist[16]), AsIs(querylist[17]), AsIs(querylist[18]), AsIs(querylist[19]), AsIs(querylist[20]), AsIs(querylist[21]), AsIs(querylist[22]), AsIs(querylist[23]),))
        conn.commit()


#run distinct pep string query on the big table

        varhgstr = "%peptide_string"
        varg22tblpepstr = "%g1000chr22%pepstr"

# select column_name from information_schema.columns where table_name like '%g1000chr22%pepstr' and column_name like '%peptide_string';

        print(cur.mogrify("select column_name from information_schema.columns where table_name like \'%s\' and column_name like \'%s\';",(AsIs(varg22tblpepstr),AsIs(varhgstr),)))
        cur.execute("select column_name from information_schema.columns where table_name like \'%s\' and column_name like \'%s\';",(AsIs(varg22tblpepstr),AsIs(varhgstr),))
#load ersults into list :

        query2list()


        print(cur.mogrify("create table allchpepstrcount as select %s as pepstr,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom ;",(AsIs(querylist[0]),AsIs(querylist[0]),AsIs(querylist[0]), AsIs(querylist[1]),AsIs(querylist[1]),AsIs(querylist[1]), AsIs(querylist[2]),AsIs(querylist[2]),AsIs(querylist[2]), AsIs(querylist[3]),AsIs(querylist[3]),AsIs(querylist[3]), AsIs(querylist[4]),AsIs(querylist[4]),AsIs(querylist[4]), AsIs(querylist[5]),AsIs(querylist[5]),AsIs(querylist[5]), AsIs(querylist[6]),AsIs(querylist[6]),AsIs(querylist[6]), AsIs(querylist[7]),AsIs(querylist[7]),AsIs(querylist[7]), AsIs(querylist[8]),AsIs(querylist[8]),AsIs(querylist[8]), AsIs(querylist[9]),AsIs(querylist[9]),AsIs(querylist[9]), AsIs(querylist[10]),AsIs(querylist[10]),AsIs(querylist[10]),)))

        cur.execute("create table allchpepstrcount as select %s as pepstr,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom ;",(AsIs(querylist[0]),AsIs(querylist[0]),AsIs(querylist[0]), AsIs(querylist[1]),AsIs(querylist[1]),AsIs(querylist[1]), AsIs(querylist[2]),AsIs(querylist[2]),AsIs(querylist[2]), AsIs(querylist[3]),AsIs(querylist[3]),AsIs(querylist[3]), AsIs(querylist[4]),AsIs(querylist[4]),AsIs(querylist[4]), AsIs(querylist[5]),AsIs(querylist[5]),AsIs(querylist[5]), AsIs(querylist[6]),AsIs(querylist[6]),AsIs(querylist[6]), AsIs(querylist[7]),AsIs(querylist[7]),AsIs(querylist[7]), AsIs(querylist[8]),AsIs(querylist[8]),AsIs(querylist[8]), AsIs(querylist[9]),AsIs(querylist[9]),AsIs(querylist[9]), AsIs(querylist[10]),AsIs(querylist[10]),AsIs(querylist[10]),))
        conn.commit()


#create table allchpepstrcountsum as select pepstr,sum(count) from allchpepstrcount group by pepstr;

        print(cur.mogrify("create table %s as select row_number() over() as str_rank,pepstr,strsum from (select pepstr,sum(count) as strsum from %s group by pepstr order by strsum desc) as table1;",(AsIs(varallchpepstrcountsum),AsIs(varallchpepstrcount),)))
        cur.execute("create table %s as select row_number() over() as str_rank,pepstr,strsum from (select pepstr,sum(count) as strsum from %s group by pepstr order by strsum desc) as table1;",(AsIs(varallchpepstrcountsum),AsIs(varallchpepstrcount),))
        conn.commit()
# create table test1 as select row_number() over() as str_rank,pepstr,strsum from (select pepstr,sum(count) as strsum from allchpepstrcount group by pepstr order by strsum desc) as table1;

    if args.add_uniq_pepstring_num:

        varallchpepstrcountsum="allchpepstrcountsum"
        varnumtable = args.add_uniq_pepstring_num+"num"

# create new table , alter it and add new columns  , update them with new info.

        check_overwrite_table(varnumtable)

        print(cur.mogrify("create table %s as select * from %s ",(AsIs(varnumtable),AsIs(args.add_uniq_pepstring_num))))
        cur.execute("create table %s as select * from %s ",(AsIs(varnumtable),AsIs(args.add_uniq_pepstring_num)))
        conn.commit()

        varhgstr = "%peptide_string"

        print(cur.mogrify("select column_name from information_schema.columns where table_name = \'%s\' and column_name like \'%s\';",(AsIs(args.add_uniq_pepstring_num),AsIs(varhgstr),)))
        cur.execute("select column_name from information_schema.columns where table_name = \'%s\' and column_name like \'%s\';",(AsIs(args.add_uniq_pepstring_num),AsIs(varhgstr),))
#load ersults into list :

        for hg1 in query2list():

            varhg1num = hg1+"_num"

            print(cur.mogrify("alter table %s add column %s text;",(AsIs(varnumtable),AsIs(varhg1num),)))
            cur.execute("alter table %s add column %s text;",(AsIs(varnumtable),AsIs(varhg1num),))
            conn.commit()


            print(cur.mogrify("update %s set %s = str_rank from allchpepstrcountsum where %s.%s = allchpepstrcountsum.pepstr;",(AsIs(varnumtable),AsIs(varhg1num),AsIs(varnumtable),AsIs(hg1),)))
            cur.execute("update %s set %s = str_rank from allchpepstrcountsum where %s.%s = allchpepstrcountsum.pepstr;",(AsIs(varnumtable),AsIs(varhg1num),AsIs(varnumtable),AsIs(hg1),))
            conn.commit()


        #update g1000chr1annsorted2sorted_by_gene_posal2pnoduppepstrnum set hg96_num = str_rank from allchpepstrcountsum where g1000chr1annsorted2sorted_by_gene_posal2pnoduppepstrnum.hg00096peptide_string = allchpepstrcountsum.pepstr;


#         print(cur.mogrify("create table allchpepstrcount as select %s as pepstr,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom union all select %s,count(%s),chrom from allchpepstr group by %s,chrom ;",(AsIs(querylist[0]),AsIs(querylist[0]),AsIs(querylist[0]), AsIs(querylist[1]),AsIs(querylist[1]),AsIs(querylist[1]), AsIs(querylist[2]),AsIs(querylist[2]),AsIs(querylist[2]), AsIs(querylist[3]),AsIs(querylist[3]),AsIs(querylist[3]), AsIs(querylist[4]),AsIs(querylist[4]),AsIs(querylist[4]), AsIs(querylist[5]),AsIs(querylist[5]),AsIs(querylist[5]), AsIs(querylist[6]),AsIs(querylist[6]),AsIs(querylist[6]), AsIs(querylist[7]),AsIs(querylist[7]),AsIs(querylist[7]), AsIs(querylist[8]),AsIs(querylist[8]),AsIs(querylist[8]), AsIs(querylist[9]),AsIs(querylist[9]),AsIs(querylist[9]), AsIs(querylist[10]),AsIs(querylist[10]),AsIs(querylist[10]),)))












# *************************************************************8
#multi core section
#select core num and execute function in pool
#function should be in top level so disable cache exeption

    # if args.multi_core_num:
    #
    #     if __name__ == '__main__':
    #         logger = mp.log_to_stderr()
    #         logger.setLevel(logging.DEBUG)
    #
    #         if args.multi_core_num == "max":
    #
    #             max_cpu = mp.cpu_count()
    #             pool = mp.Pool(processes=max_cpu)
    #             print "cpu count", int(max_cpu)
    #             # results = [pool.apply_async(multiquery, (setting,)) for setting in range(2)]
    #             for setting in range(2):
    #                 pool.apply_async(multiquery,(setting,))
    #             # pool.apply_async(multiquery(1))
    #
    #         if isInt(args.multi_core_num):
    #             pool = mp.Pool(processes=int(args.multi_core_num))
    #             print "int ok", args.multi_core_num
    #             results = [pool.apply_async(multifunc, (setting,)) for setting in range(2)]

        # print 'Ordered results using pool.apply_async():'

    # for result in results:
    #     # print '\t', result.get()
    #     # print '\t', result.ready()
    #     print '\t', result.successful()
            # with open(settings_file) as f:
#                 for line in f:
# #         config = script2p+" "+line
# #         print "command :", config
# #         settings_list.append(config)


#end of program execution
except (KeyboardInterrupt, SystemExit):
    print "\n Program interrupted  ! \n Clean up in progress..."
    interrans = raw_input("Are you sure you want to cleanup stuff ? (yes/no)")
    if interrans == "yes":
        print "ok doing cleanup stuff, clean up stuff disabled for now"
        # cleanup_err_tables()
    else:
        print "ok , leaving all untouched.."
        sys.exit()





