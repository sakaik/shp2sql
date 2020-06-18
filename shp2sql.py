#!/usr/bin/python3
#
# shp2sql.py 
#    since 2020/01/20
#       by @sakaik
#  License: GPLv2 (https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
#

import sys
import struct
import argparse
import os


DEFAULT_CHARSET = "utf-8"
DEFAULT_SRID = 4326
DEFAULT_SHAPE_COLUMN_NAME="SHAPE"

INTBYTES=4
DOUBLEBYTES=8

#---------------------------------------
class OPT_STRUCTURE:
  fnbase = "" # with fullpath but no fn-ext
  filepath = ""
  tablename = ""
  charset = DEFAULT_CHARSET
  #charset = "cp932"
  srid = DEFAULT_SRID
  shape_column_name = DEFAULT_SHAPE_COLUMN_NAME
  output_format = "mysql"
  add_drop_table = False
  debug_mode=0

#---------------------------------------
class DBF_STRUCTURE:
  nofrecords=0
  headersize=0
  recordsize=0
  columnname=[]
  type=[]
  size=[]
  prec=[]
  
  dbfdata=[]
  
  @classmethod
  def row_format_str(cls):
    fmtstr = "c"
    for i in range(cls.nofcolumns()):
      typechar=""
      currenttype = cls.type[i]
      if currenttype=="N" or currenttype=="C":
        typechar="s"
      if currenttype=="D":
        typechar="s"
      if currenttype=="F":
        typechar="s"
      if currenttype=="L":
        typechar=""             #TODO???
      if typechar!="":
        fmtstr += str(cls.size[i]) + typechar
      else:
        print ("Unknown data type: "+ currenttype)
        exit()
    return fmtstr
  
  @classmethod
  def nofcolumns(cls):
    return len(cls.columnname)

class SHP_RECORD_STRUCTURE:
  def __init__(self):
    self.parts = []
    self.pointsX = []
    self.pointsY = []
    self.hdr_recno, self.hdr_content_length = 0,0
    self.xmin, self.ymin, self.xmax, self.ymax = 0,0,0,0
    self.nofparts, self.nofpoints, self.x, self.y = 0,0,0,0
  hdr_recno=0
  hdr_content_length=0
  shapetype=""
  xmin=0
  ymin=0
  xmax=0
  ymax=0
  nofparts=0
  nofpoints=0
#  parts=[]
#  pointsX=[]
#  pointsY=[]
  x=0
  y=0
  
class SHP_STRUCTURE:
  filecode=""
  fileversion=""
  filelength=""
  shapetype=""
  xmin=0
  ymin=0
  xmax=0
  ymax=0
  zmin=0
  zmax=0
  mmin=0
  mmax=0
  
  shpdata=[]
  
  @classmethod
  def nofrecords(self):
    return len(self.shpdata)
  
  #SHAPE_TYPEs
  #  1 Point        implemented!
  #  3 PolyLine     Not yet implement
  #  5 Polygon      implemented!
  #  8 MultiPoint   Not yet implement
  # 11 PointZ       Not yet implement
  # 13 PolyLineZ    Not yet implement
  # 15 PolygonZ     Not yet implement
  # 18 MultiPointZ  Not yet implement
  # 21 PointM       Not yet implement
  # 23 PolyLineM    Not yet implement
  # 25 PolygonM     Not yet implement
  # 28 MultiPointM  Not yet implement
  # 31 MyltiPatch   Not yet implement
  
  
#---------------------------------------
OPT=OPT_STRUCTURE
DBF=DBF_STRUCTURE
SHP=SHP_STRUCTURE
#---------------------------------------
def main():
  #param処理
  if (proc_arg() == False):
    exit()
  dbf_main()
  shp_main()
  output_main(OPT.output_format)
  
#---------------------------------------



#---------------------------------------
def proc_arg():
  parser = argparse.ArgumentParser()
  parser.add_argument("input_filename", help="shapefile name")
  parser.add_argument("-c", "--charset", help="Set chracter set(not yet)(default:utf-8;but currently cp932 for develop)")
  parser.add_argument("-s", "--srid", help="Set SRID(default:4326)")
  parser.add_argument("-d", "--add-drop-table", help="Adding DROP TABLE before CREATE TABLE.", action="store_true")
  parser.add_argument("-x", "--summary", help="display shapefile summary for development.", action="store_true")
  parser.add_argument("-T", "--tablename", help="Set output table name")

#  parser.add_argument("-o", "--outputfile", help="Set output filename(Not yet)")
#  parser.add_argument("-t", "--outputtype", help="Set output type(Not yet)", choices=["mysql","text"])
#  parser.add_argument("-F", "--force", help="Force execute")
#  parser.add_argument("", "--no-dbf-output", help="For Develop: output without dbf info.", action="" )
  args=parser.parse_args()
  
  input_filename=args.input_filename
  #----for develop-------------
  if input_filename=="x":  #for develop
    input_filename = "data/N03-19_12_190101.shp"
  if input_filename=="y":  #for develop
    input_filename = "data/h27ka12.shp"
  if input_filename=="z":  #for develop
    input_filename = "data2/A16-15_12_DID.shp"
  
  #----------------------------
  shp_fnonly = os.path.basename(input_filename)
  filepath=os.path.dirname(input_filename)
  fnbase=os.path.splitext(shp_fnonly)[0]
  dbf_fnonly=fnbase+".dbf"
  #存在チェック
  if os.path.exists( os.path.join(filepath, "", shp_fnonly))==False:
    print ("No such file: "+ os.path.join(filepath, "", shp_fnonly))
    exit()
  if os.path.exists( os.path.join(filepath, "", dbf_fnonly))==False:
    print ("No such file: "+ os.path.join(filepath, "", dbf_fnonly))
    exit()
  
  OPT.fnbase = fnbase
  OPT.filepath=filepath
  OPT.tablename = fnbase.replace("-","_")
  if args.tablename:
    OPT.tablename = args.tablename
  if args.srid:
    OPT.srid = args.srid

  if args.add_drop_table:
    OPT.add_drop_table = True
  if args.summary:
    OPT.output_format = "summary"
  if args.charset:
    OPT.charset = args.charset

  return True

#---------------------------------------
def dbf_main():
  filename = OPT.fnbase + ".dbf"
  filefullpath = os.path.join(OPT.filepath, "", filename)
  print("-- Start reading file: "+ filename)
  fc = open(filefullpath, "rb").read()
  pos=dbf_read_header(fc)
  pos=dbf_read_data(fc,pos)
  
#---------------------------------------
def dbf_read_header(fc):
  pos=0
  hdr=struct.unpack_from("<IIHH", fc, pos)
  DBF.nofrecords, DBF.headersize, DBF.recordsize=hdr[1],hdr[2],hdr[3]
  dbg_print (DBF.recordsize)
  
  pos=32
  
  while struct.unpack_from("B", fc, pos)[0] != 0x0d:
    hdr=struct.unpack_from("<11ssIBB", fc, pos)
    DBF.columnname.append(hdr[0].decode().strip("\0"))
    DBF.type.append(hdr[1].decode())
    DBF.size.append(hdr[3])
    DBF.prec.append(hdr[4])
    dbg_print (hdr)
    pos +=32
  
  pos += 1  #add pos for 0x0d terminal byte
  return pos


#---------------------------------------
def dbf_read_data(fc, pos):
  #ここでレコードの取得用型文字列を作成しておく
  row_format_str = DBF.row_format_str()
  for recno in range(DBF.nofrecords):
    data=struct.unpack_from(row_format_str, fc, pos)
    samplestr=""
    rowdata=[]
    for c in range(DBF.nofcolumns()):
      rowdata.append(data[c+1].decode(OPT.charset).strip("\0").strip())
    
    pos += DBF.recordsize
    DBF.dbfdata.append(rowdata)


#---------------------------------------
def shp_main():
  filename = OPT.fnbase + ".shp"
  filefullpath = os.path.join(OPT.filepath, "", filename)
  print("-- Start reading file: "+ filename)
  fc = open(filefullpath, "rb").read()
  pos=0
  pos=shp_read_header(fc, pos)
  pos=shp_read_data(fc, pos)


#---------------------------------------
def shp_read_header(fc, pos):
  hdr=struct.unpack_from(">iiiiiiI", fc, pos)
  SHP.filecode, SHP.filelength = hdr[0], hdr[6]
  pos += 4*7

  hdr=struct.unpack_from("<IIdddddddd", fc, pos)
  SHP.fileversion, SHP.shapetype = hdr[0], hdr[1]
  SHP.xmin, SHP.ymin, SHP.xmax, SHP.ymax = hdr[2],  hdr[3], hdr[4], hdr[5]
  SHP.zmin, SHP.zmax, SHP.mmin, SHP.mmax = hdr[6],  hdr[7], hdr[8], hdr[9]
  pos += 4*2 + 8*8
  return pos


#---------------------------------------
def shp_read_data(fc, pos):
  notimplemented=0
  if SHP.shapetype==0:   #NULL_SHAPE #TODO
    notimplemented=1
  elif SHP.shapetype==1:   #POINT #TODO
    pos=shp_read_data_point(fc, pos)
#    notimplemented=1
  elif SHP.shapetype==3:   #POLILINE #TODO
    notimplemented=1
  elif SHP.shapetype==5:   #POLYGON
    pos=shp_read_data_polygon(fc, pos)
  elif SHP.shapetype==8:   #MULTIPOINT #TODO
    notimplemented=1
  else:
    notimplemented=1
    
  if notimplemented==1:
    print("Shape type "+ str(SHP.shapetype) +" is not implemented yet.")
    exit()
  return pos


#---------------------------------------
def shp_read_data_point(fc, pos):
  while True:
    if pos >= w2b(SHP.filelength):
      print("-- finished shp file.")
      break
    rec=SHP_RECORD_STRUCTURE()
    #Record header
    hdr=struct.unpack_from(">II", fc, pos)
    rec.hdr_recno, rec.hdr_content_length = hdr[0], hdr[1]
    pos += 4*2
    
    #Record body(1)
    bdy=struct.unpack_from("<Idd", fc, pos)
    
    rec.shapetype=bdy[0]
    rec.x, rec.y = bdy[1], bdy[2]
    pos += 8*2 + 4*1
    SHP.shpdata.append(rec) 

  return pos

#---------------------------------------
def shp_read_data_polygon(fc, pos):
  while True:
    #print (str(pos) +" / "+ str(w2b(SHP.filelength)))
    if pos >= w2b(SHP.filelength):
      print("-- finished shp file.")
      break
    rec=SHP_RECORD_STRUCTURE()
    #Record header
    hdr=struct.unpack_from(">II", fc, pos)
    rec.hdr_recno, rec.hdr_content_length = hdr[0], hdr[1]
    pos += 4*2
    
    #Record body(1)
    bdy=struct.unpack_from("<IddddII", fc, pos)
    
    rec.shapetype=bdy[0]
    rec.xmin, rec.ymin, rec.xmax, rec.ymax = bdy[1], bdy[2], bdy[3], bdy[4]
    rec.nofparts, rec.nofpoints = bdy[5],bdy[6]
    pos += 8*4 + 4*3
    
    #--parts
    parts=struct.unpack_from("<"+ str(rec.nofparts) +"I", fc, pos)
    for part in range(rec.nofparts):
      rec.parts.append(parts[part])
    
    nextpartno=1
    if nextpartno<rec.nofparts:
      nextpartstartpoint=parts[nextpartno]
    else:
      nextpartstartpoint=-1    
    pos += 4*rec.nofparts
    
    #--points
    for pointnum in range(rec.nofpoints):
      bdy=struct.unpack_from("<dd", fc, pos)
      rec.pointsX.append(bdy[0])
      rec.pointsY.append(bdy[1])
      pos += 8*2
    SHP.shpdata.append(rec) 

  return pos


#---------------------------------------
def output_main(output_format):
  if output_format=="mysql":
    output_mysql_1()
  elif output_format=="summary":
    output_summary()
  elif output_format=="csv":
    return


#---------------------------------------
def output_mysql_1():  #INS and UPDATE version
  cols_for_ins=""
  ddl = ""
  
  if OPT.add_drop_table:
    ddl += "DROP TABLE IF EXISTS {};\n".format(OPT.tablename)
  ddl += "CREATE TABLE {}(\n".format(OPT.tablename)
  ddl +="  RECID  INTEGER,\n"
  cols_for_ins = "RECID"
  for i in range(len(DBF.columnname)):
    fieldtype = get_mysql_column_type(DBF.type[i], DBF.size[i], DBF.prec[i])

    ddl += "  {} {},\n".format(DBF.columnname[i], fieldtype)
    cols_for_ins += ","+DBF.columnname[i]
  
  ddl += "  {} GEOMETRY SRID {}\n".format(OPT.shape_column_name, OPT.srid)
  ddl += ");\n"
  print(ddl)
  
  #dbf file
  insbase= "INSERT INTO {} ({}) VALUES (".format(OPT.tablename, cols_for_ins)
  
  ins = ""
  for recno in range(DBF.nofrecords):
    ins = ""
    ins += insbase
    ins += str(recno)
    for cno in range(DBF.nofcolumns()):
      colval = make_column_value(DBF.dbfdata[recno][cno], DBF.type[cno])
      ins += ","+ colval
    ins += ");"
    print(ins) 

  #shpfile
  print ("-- update shape data")
  for recno in range(SHP.nofrecords()):
     upd = ""
     rec=SHP.shpdata[recno]
     colwktstr = make_col_wkt_str(recno, rec)
     upd += "UPDATE {} SET {}=".format(OPT.tablename, OPT.shape_column_name)
     upd += 'ST_GeomFromText("{}",{})'.format(colwktstr, OPT.srid)
     upd += " WHERE RECID={};".format(recno)
     print(upd)


#---------------------------------------
def make_col_wkt_str(recno, rec):
  s=""
  if rec.shapetype==5:
    nextpartno=-1
    nextpartstartpoint=-1
    if rec.nofparts>1:
      nextpartno=1
      nextpartstartpoint=rec.parts[nextpartno]
      #print (rec.parts)
    s+="POLYGON(("
    #print ("nofparts:"+ str(rec.nofparts)+ "   nextpartstart:"+ str(nextpartstartpoint))
    for pointno in range(rec.nofpoints):
      s += str(rec.pointsY[pointno]) +" "+ str(rec.pointsX[pointno])
      if pointno==nextpartstartpoint-1:
        s += "),("
        if nextpartno<rec.nofparts-1:
          nextpartno += 1
          nextpartstartpoint=rec.parts[nextpartno]
          #print ("nofparts:"+ str(rec.nofparts)+ "   nextpartstart:"+ str(nextpartstartpoint))
      else:
        if (pointno != rec.nofpoints-1):
          s += ","
    s += "))"
    return s
  elif rec.shapetype==1:
    s+="POINT({} {})".format(rec.y, rec.x)
    return s
  else:
    print ("Shape type "+ str(rec.shapetype) +" is not supported yet.")


#---------------------------------------
def make_column_value(v, type):
  ret = ""
  v=v.replace("'","\'")
  if v=="":
    ret="null"
  elif type=="N":
    ret=v
  elif type=="C":
    ret="'"+ v +"'"
  else:
    ret=v    #TODO(more other types)
  return ret
#---------------------------------------
def get_mysql_column_type(fieldtype_short, fieldlen, precision):
  ret=""
  if fieldtype_short=="C":
    ret= "VARCHAR("+ str(fieldlen) +")"
  elif fieldtype_short=="N":
    if precision==0:
      if fieldlen<=4:
        ret="SMALLINT"
      elif fieldlen<=6:
        ret="INTEGER"
      elif fieldlen<=10:
        ret="BIGINT"
      else:
        ret="DECIMAL"
    else:
      ret="FLOAT"
  elif fieldtype_short=="F":
    ret="FLOAT({},{})".format(fieldlen, precision)
  elif fieldtype_short=="D":
    ret="DATE"
  else:
    ret="unknown_type"
  return ret

#---------------------------------------
def output_summary():
  str = ""
  coltypestr = ""
  for i in range(DBF.nofcolumns())	:
    coltypestr += DBF.type[i]
  str += "{}\t{}\t{}\t{}\t{}\t{}\t{}".format(
    OPT.fnbase, DBF.recordsize, SHP.filelength, SHP.shapetype, DBF.nofcolumns(), coltypestr, DBF.nofrecords)

  hdr = "fnbase\tdbf_recsize\tshp_filelen\tshptype\tdbf_colcnt\tcoltypes\tdbfreccnt"
  
  print(hdr)
  print(str)
  
#---------------------------------------
def w2b(word_value):
  return word_value*2

#---------------------------------------
def dbg_print(s):
  if (OPT.debug_mode == 1):
    print (s)
#---------------------------------------
main()

#---------------------------------------

#---------------------------------------

