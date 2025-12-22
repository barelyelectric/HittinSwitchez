What this script does:
----------------------
Scans current directory for WildTangent .wjp and .wt files, and displays current expiry dates.

Patch all .wjp and .wt files in-place with new expiry date.

Change 'test' license to 'free'.

Displays the changes made.


How the patch script works:
---------------------------
For every .WJP and .WT file in the current directory, scan-patch.py decrypts the
payload using a header-derived rolling XOR stream cipher, changes the expiry value
to hex FF FF FF FF (as per all other game files it expires 2106-02-06 22:28:15),
and changes the license string from test to free. It then rebuilds the encryption
key from the modified headers and re-encrypts the payload so the file remains valid.


How m_homes_02.wt integrity was verified post-patch:
----------------------------------------------------

`python wtextract.py m_homes_02.wt m_homes_02.wt.pwt`

`expand m_homes_02.wt.pwt -F:* m_homes_02.pwt`

`python pwtdecode.py m_homes_02.pwt > m_homes_02-orig.txt`

Repeat for the patched version (in a separate folder) except output to m_homes_02-patched.txt

Nnow compare the two files, there should be no difference.

`fc/b m_homes_02-orig.txt m_homes_02-patched.txt`


Notes:
------
requirements.txt is only needed to run wtextract.py and pwtdecode.py to verify m_homes_02.wt
Big thanks to CobySucks for purchasing the game and to Jessy (diamondman) for WTExtractor


Sources:
--------
wtextract.py & pwtdecode.py - https://github.com/diamondman/WTExtractor
