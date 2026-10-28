"""Roman Bangla adapter with common-word overrides and optional Avro engine."""
try:
    import avro as _avro
except Exception:
    _avro = None

_FALLBACK = {
    "ami":"আমি","amra":"আমরা","apni":"আপনি","tumi":"তুমি","amar":"আমার",
    "tomar":"তোমার","bangla":"বাংলা","banglay":"বাংলায়","bhalo":"ভালো",
    "valo":"ভালো","kemon":"কেমন","achen":"আছেন","achhi":"আছি","achi":"আছি",
    "korbo":"করব","koro":"করো","kore":"করে","hobe":"হবে","khub":"খুব",
    "dhonnobad":"ধন্যবাদ","shukriya":"শুকরিয়া","kothay":"কোথায়","ki":"কি",
    "keno":"কেন","na":"না","ha":"হ্যাঁ","hya":"হ্যাঁ","theke":"থেকে",
    "sob":"সব","kaj":"কাজ","shuru":"শুরু","baniye":"বানিয়ে","dao":"দাও",
    "chai":"চাই","jabo":"যাব","parbo":"পারব","hoy":"হয়","boi":"বই",
    "phone":"ফোন","laptop":"ল্যাপটপ","word":"ওয়ার্ড"
}
def roman_to_bangla(text):
    if not text: return text
    # Prefer hand-verified common forms over engine variants.
    if text.lower() in _FALLBACK:
        return _FALLBACK[text.lower()]
    if _avro is not None:
        try:
            fn=getattr(_avro,"to_bangla",None) or getattr(_avro,"parse",None)
            if callable(fn):
                result=fn(text)
                if isinstance(result,str): return result
                for attr in ("bangla","text","output"):
                    v=getattr(result,attr,None)
                    if isinstance(v,str): return v
        except Exception:
            pass
    return text
