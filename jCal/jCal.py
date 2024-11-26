import icalendar


TYPE_MAP = {
    icalendar.vText: "text",
}

def convert_property(prop):
    if isinstance(prop, icalendar.vText):
        return str(prop)
    if isinstance(prop, icalendar.vDate):
        return f"{prop.dt.year:04}{prop.dt.month:02}{prop.dt.day:02}"
    if isinstance(prop, icalendar.vDatetime):
        return f"{prop.dt.year:04}{prop.dt.month:02}{prop.dt.day:02}T{prop.dt.hour:02}{prop.dt.minute:02}{prop.dt.second:02}"


def to_jcal(comp: icalendar.Component):
    properties = []
    for name, value in comp.items():
        properties.append([name.lower(), dict(value.params), TYPE_MAP.get(value.__class__), str(value)])
    return [
        comp.name.lower(),
        [properties],
        [to_jcal(subcomp) for subcomp in comp.subcomponents],
    ]


def from_ical(ical_string):
    ical = icalendar.Component.from_ical(ical_string)
    return to_jcal(ical)
