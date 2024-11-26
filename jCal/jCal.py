from datetime import date, datetime, time, timedelta
import icalendar


def convert_property(name, prop):
    name = name.lower()
    params = dict(prop.params)
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
        if params.get('VALUE') == 'DATE':
            params.pop('VALUE')
        return [name, params, "date", val]
    if isinstance(prop, icalendar.vDatetime):
        tzid = icalendar.prop.tzid_from_dt(dt)
        val = prop.dt.strftime("%Y-%m-%dT%H:%M:%S")
        if tzid == 'UTC':
            val += "Z"
        elif tzid:
            params.update({'TZID': tzid})
        return [name, params, "date-time", val]
    return [name, params, "unknown", str(prop)]


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
