from .guards.injection import InjectionGuard
from .guards.pii import PIIGuard
from .guards.topic import TopicGuard
from .guards.output import LeakGuard, GroundednessGuard, FormatGuard

def build_guards(policy, delay_ms=0):
    i, o = policy["input"], policy["output"]
    inp = [InjectionGuard(i["injection_threshold"], delay_ms), PIIGuard(delay_ms),
           TopicGuard(i["blocked_topics"], delay_ms)]
    out = [LeakGuard(o["canaries"]), GroundednessGuard(), FormatGuard(o["max_len"]), PIIGuard()]
    return inp, out