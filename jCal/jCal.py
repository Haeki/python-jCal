from datetime import date, datetime, time, timedelta
import icalendar


def convert_property(name, prop):
    name = name.lower()
    params = {k.lower(): v for k, v in prop.params.items() if k.lower()}
    print("prop type", type(prop))
    if value := params.pop('value', None):
        if value.lower() == 'binary':
            return [name, params, "binary", str(prop)]
        if value.lower() == 'date':
            val = prop.dt.isoformat()
            return [name, params, "date", val]
        if value.lower() == 'boolean':
            return [name, params, "boolean", str(prop).lower() == 'true']
    if isinstance(prop, icalendar.vBoolean):
        return [name, params, "boolean", bool(prop)]
    if isinstance(prop, icalendar.vDDDTypes):
        dt = prop.dt
        if isinstance(dt, datetime):
            prop = icalendar.vDatetime(dt)
        elif isinstance(dt, date):
            prop = icalendar.vDate(dt)
        elif isinstance(dt, timedelta):
            prop = icalendar.vDuration(dt)
        elif isinstance(dt, time):
            prop = icalendar.vTime(dt)
        elif isinstance(dt, tuple) and len(dt) == 2:
            prop = icalendar.vPeriod(dt)
        else:
            raise ValueError(f'Unknown date type: {type(dt)}')
    if isinstance(prop, icalendar.vText):
        return [name, params, "text", str(prop)]
    if isinstance(prop, icalendar.vDate):
        val = prop.dt.isoformat()
        return [name, params, "date", val]
    if isinstance(prop, icalendar.vDatetime):
        tzid = icalendar.prop.tzid_from_dt(dt)
        val = prop.dt.strftime("%Y-%m-%dT%H:%M:%S")
        if tzid == 'UTC':
            val += "Z"
        elif tzid:
            params.update({'TZID': tzid})
        return [name, params, "date-time", val]
    if isinstance(prop, icalendar.vBinary):
        return [name, params, "binary", str(prop)]
    print(f"Unknown type: {type(prop)}")
    return [name, params, type(prop), str(prop)]


def to_jcal(comp: icalendar.Component):
    properties = [convert_property(name, value) for name, value in comp.items()]
    return [
        comp.name.lower(),
        properties,
        [to_jcal(subcomp) for subcomp in comp.subcomponents],
    ]


def from_ical(ical_string):
    ical = icalendar.Component.from_ical(ical_string)
    return to_jcal(ical)
