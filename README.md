# shp2sql.py
  
  Using this program, you can make SQL scripts for importing spatial data(shapefile) to MySQL Server.
  
To use this, you need Python 3.

# How to use

1. Prepare the shapefile. (at least you needs *.shp, *.dbf)
2. run 
```
$ ./shp2sql.py input.shp > output.sql
```
 or 

```
$ ./shp2sql.py input.shp | mysql -u*username* -p *database_name*
```

If the character set of the input file is not utf8(e.g. cp932), you can specify the character set by -c option.

```
$ ./shp2sql.py -c cp932 input.shp > output.sql
```


# Plans for future improvements

- Supporting shapefile type 3
- Supporting shapefile type 23
- Adding some error handlings
- Changing to an SQL script that processes in a single transaction
- Changing to an SQL script that uses only INSERT statements(In the current version, it does UPDATE after INSERT)




# Request for you

 Please let me know if you find a shapefile that gives you an error with this program. (Other than shape type 3 and 23.)
 