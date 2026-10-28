from gboard_pc_system import correction_for
from avro_support import roman_to_bangla

cases=[("teh","the"),("Teh","The"),("TEH","THE"),("recieve","receive"),("unknown",None),("",None),("the",None)]
for src, expected in cases:
    got=correction_for(src,False)
    assert got==expected,(src,expected,got)
for src,expected in [("ami","আমি"),("apni","আপনি"),("banglay","বাংলায়"),("khub","খুব")]:
    got=roman_to_bangla(src)
    assert got==expected,(src,expected,got)
print("PASS: 7 English correction + 4 Bangla adapter smoke tests")
