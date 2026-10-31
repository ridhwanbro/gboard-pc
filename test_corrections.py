from gboard_pc_system import correction_for, replacement_for
from avro_support import roman_to_bangla

cases=[("teh","the"),("Teh","The"),("TEH","THE"),("recieve","receive"),("unknown",None),("",None),("the",None)]
for src, expected in cases:
    got=correction_for(src,False)
    assert got==expected,(src,expected,got)
for src,expected in [("ami","আমি"),("apni","আপনি"),("banglay","বাংলায়"),("khub","খুব"),
                     ("ami banglay gan gai","আমি বাংলায় গান গাই")]:
    got=roman_to_bangla(src)
    assert got==expected,(src,expected,got)
print("PASS: 7 English correction + 5 Bangla adapter smoke tests")
assert correction_for("speling",False)=="spelling"
print("PASS: offline English dictionary correction")
for word, bangla, suffix, expected in [
    ("ami",True," ","আমি "),
    ("ami",True,",","আমি,"),
    ("teh",False," ","the "),
    ("unknown",True," ",None),
]:
    got=replacement_for(word,bangla,suffix)
    assert got==expected,(word,bangla,suffix,expected,got)
print("PASS: word replacement preserves spaces and punctuation")

