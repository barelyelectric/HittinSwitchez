What is this all about?
-----------------------
In the 2002 Eazy-E PC game Hittin' Switchez (CD/DVD release of Impact of a Legend), 
there are a number of textures that were (accidentally?) set to expire three months after 
their export date which result in loading errors and broken textures in-game. They are:

watts<br>
`2002-04-09 02:42:27 UTC t_public.wjp`<br>
`2002-04-09 07:56:44 UTC t_watts_1.wjp`<br>
`2002-04-08 10:37:49 UTC t_wujiang.wjp`<br>

ingle<br>
`2002-04-09 07:44:39 UTC t_compton.wjp`<br>
`2002-04-09 02:42:27 UTC t_inglewood.wjp`<br>
`2002-04-09 02:42:27 UTC t_inglewood_1.wjp`<br>
`2002-04-09 02:42:27 UTC t_inglewood_2.wjp`<br>
`2002-04-09 02:42:27 UTC t_public.wjp`<br>
`2002-04-09 07:51:57 UTC t_wall.wjp`<br>

crenshaw<br>
`2002-04-09 02:42:27 UTC t_public.wjp`<br>
`2002-04-09 07:51:57 UTC t_wall.wjp`<br>

compton<br>
`2002-04-09 07:44:14 UTC m_homes_02.wt`<br>
`2002-04-09 07:44:39 UTC t_compton.wjp`<br>
`2002-04-09 02:42:27 UTC t_public.wjp`<br>
`2002-04-09 07:51:57 UTC t_wall.wjp`<br>

What this script (patchwt.py) does:
-----------------------------------
* Scans current directory for WildTangent .WJP and .WT files, and displays expiry dates.

* Patches all .WJP and .WT files in-place with new expiry date.

* Changes 'test' license to 'free'.

* Displays the changes made.


How the patch script works:
---------------------------
For every .WJP and .WT file in the current directory, scan-patch.py decrypts the
payload using a header-derived rolling XOR stream cipher, changes the expiry value
to hex `FF FF FF FF` (as per all other game files it expires 2106-02-06 22:28:15),
and changes the license string from test to free. It then rebuilds the encryption
key from the modified headers and re-encrypts the payload so the file remains valid.


How m_homes_02.wt integrity was verified post-patch:
----------------------------------------------------
For the .WJP files the .JPG can be extracted and binary compared to confirm there are 
no changes to the image post-patch. For the .WT file there's a few extra steps. None 
of this needs to actually be done after the patch, I just wanted to show how I made 
sure we only modified the expiry data and nothing else.
```
python wtextract.py m_homes_02.wt m_homes_02.wt.pwt
```
```
expand m_homes_02.wt.pwt -F:* m_homes_02.pwt
```
```
python pwtdecode.py m_homes_02.pwt > m_homes_02-orig.txt
```
In a separate folder repeat the process for the patched file, output to `m_homes_02-patched.txt`
<br><br>
Now compare the two files, there should be no difference.
```
fc/b m_homes_02-orig.txt m_homes_02-patched.txt
```

Notes:
------
* VM files are here https://archive.org/details/hittin-switchez

* `requirements.txt` is only needed to run `wtextract.py` and `pwtdecode.py` to verify `m_homes_02.wt`

* Big thanks to @cobysucks for providing the game and to Jessy (diamondman) for WTExtractor


Todo:
-----
* Create standalone patcher utility and/or diff patches

Sources:
--------
wtextract.py & pwtdecode.py - https://github.com/diamondman/WTExtractor
