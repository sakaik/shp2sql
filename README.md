# shp2sql.py

  This program is making SQLs for importing spatial data (shapefile) to MySQL Server.

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


# What's plan to next?

- support shape type 3
- support shape type 23
- change output sql ('update after insert' to 'single insert')
- to single transaction
- some error handlings



# Request for you

 When you find the shapefile that cause error in this program, please let me know it.
(Other than shape type 3 and 23.)
 