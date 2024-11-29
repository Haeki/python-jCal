from datetime import date, datetime, time, timedelta, UTC
import json
import icalendar

RAISE_ON_INVALID = object()
INVALID_DEFAULTS = {
    "float": 0.0,
    "integer": 0,
}


def _vTime_from_ical(ical):
    try:
        timetuple = (int(ical[:2]), int(ical[2:4]), int(ical[4:6]))
        if ical.endswith("Z"):
            return time(*timetuple, tzinfo=UTC)
        return time(*timetuple)
    except Exception as e:
        raise ValueError(f"Expected time, got: {ical}") from e


icalendar.prop.vTime.from_ical = _vTime_from_ical


def date_to_jcal(
    prop: icalendar.vDate | icalendar.vDDDTypes | icalendar.vText | date, params, name
):
    dt: date
    if isinstance(prop, icalendar.vText):
        dt = icalendar.vDate.from_ical(prop)
    elif _dt := getattr(prop, "dt", None):
        dt = _dt
    else:
        dt = prop
    return [name, params, "date", dt.isoformat()]


def datetime_to_jcal(
    prop: icalendar.vDatetime | icalendar.vDDDTypes | icalendar.vText | datetime,
    params,
    name,
):
    dt: datetime
    if isinstance(prop, icalendar.vText):
        dt = icalendar.vDatetime.from_ical(prop)
    elif _dt := getattr(prop, "dt", None):
        dt = _dt
    else:
        dt = prop
    tzid = icalendar.prop.tzid_from_dt(dt)
    val = dt.strftime("%Y-%m-%dT%H:%M:%S")
    if tzid == "UTC":
        val += "Z"
    elif tzid:
        params.update({"tzid": tzid})
    return [name, params, "date-time", val]


def time_to_jcal(prop: icalendar.vTime | icalendar.vText | time, params, name):
    dt: time
    if isinstance(prop, icalendar.vText):
        dt = icalendar.vTime.from_ical(prop)
    elif (_dt := getattr(prop, "dt", None)) is not None:
        dt = _dt
    else:
        dt = prop
    tzid = icalendar.prop.tzid_from_dt(dt)
    val = dt.strftime("%H:%M:%S")
    if tzid == "UTC":
        val += "Z"
    elif tzid:
        params.update({"tzid": tzid})
    return [name, params, "time", val]


def period_to_jcal(prop: icalendar.vPeriod | icalendar.vDDDTypes, params, name):
    if isinstance(prop, icalendar.vDDDTypes):
        prop = icalendar.vPeriod(prop.dt)
    if prop.by_duration:
        val = [
            datetime_to_jcal(prop.start, {}, "start")[-1],
            CONVERSION_MAP["duration"](prop.duration, {}, "duration")[-1],
        ]
    else:
        val = [
            datetime_to_jcal(prop.start, {}, "start")[-1],
            datetime_to_jcal(prop.end, {}, "end")[-1],
        ]
    return [name, params, "period", val]


def utc_offset_to_jcal(
    prop: icalendar.vUTCOffset | icalendar.vText | timedelta, params, name
):
    td: timedelta
    if isinstance(prop, icalendar.vText):
        td = icalendar.vUTCOffset.from_ical(prop)
    elif (_td := getattr(prop, "td", None)) is not None:
        td = _td
    else:
        td = prop
    sign = "+" if td >= timedelta(0) else "-"
    days, seconds = td.days, td.seconds
    hours = abs(days * 24 + seconds // 3600)
    minutes = abs((seconds % 3600) // 60)
    seconds = abs(seconds % 60)
    if seconds:
        val = f"{sign}{hours:02}:{minutes:02}:{seconds:02}"
    else:
        val = f"{sign}{hours:02}:{minutes:02}"
    return [name, params, "utc-offset", val]


def duration_to_jcal(prop: icalendar.vDuration | timedelta, params, name):
    if isinstance(prop, timedelta):
        prop = icalendar.vDuration(prop)
    return [
        name,
        params,
        "duration",
        prop.to_ical().decode("utf-8"),
    ]


def boolean_to_jcal(prop: icalendar.vBoolean, params, name):
    if isinstance(prop, icalendar.vText):
        return [name, params, "boolean", prop.to_ical() == b"TRUE"]
    elif isinstance(prop, int):
        return [name, params, "boolean", bool(prop)]
    else:
        raise ValueError(f"Invalid boolean value: {prop}")


def float_to_jcal(prop: icalendar.vFloat, params, name):
    try:
        return [name, params, "float", float(prop)]
    except ValueError as e:
        if INVALID_DEFAULTS["float"] is RAISE_ON_INVALID:
            raise e
        return [name, params, "float", INVALID_DEFAULTS["float"]]


def integer_to_jcal(prop: icalendar.vInt, params, name):
    try:
        return [name, params, "integer", int(prop)]
    except ValueError as e:
        if INVALID_DEFAULTS["integer"] is RAISE_ON_INVALID:
            raise e
        return [name, params, "integer", INVALID_DEFAULTS["integer"]]


def recur_to_jcal(prop: icalendar.vRecur, params, name):
    val = {}
    for rule_k, rule_v in prop.sorted_items():
        rule_k = rule_k.lower()
        if rule_k in ["freq", "wkst"]:
            if not isinstance(rule_v, str):
                if len(rule_v) > 1:
                    raise ValueError(
                        f"Invalid value for {rule_k}: {rule_v} (must be a single string)"
                    )
                rule_v = rule_v[0]
            val[rule_k] = str(rule_v)
        elif rule_k in ["interval", "count"]:
            if not isinstance(rule_v, int):
                if len(rule_v) > 1:
                    raise ValueError(
                        f"Invalid value for {rule_k}: {rule_v} (must be a single integer)"
                    )
                rule_v = rule_v[0]
            val[rule_k] = int(rule_v)
        elif rule_k in ["until"]:
            if isinstance(rule_v, (list, tuple)):
                if len(rule_v) > 1:
                    raise ValueError(
                        f"Invalid value for {rule_k}: {rule_v} (must be a single datetime)"
                    )
                rule_v = rule_v[0]
            if isinstance(rule_v, datetime):
                val[rule_k] = datetime_to_jcal(rule_v, {}, "until")[-1]
            elif isinstance(rule_v, date):
                val[rule_k] = date_to_jcal(rule_v, {}, "until")[-1]
            else:
                raise ValueError(
                    f"Invalid value for {rule_k}: {rule_v} (must be a datetime or date)"
                )
        else:
            if not isinstance(rule_v, (list, tuple)):
                rule_v = [rule_v]
            vals = []
            for v in rule_v:
                if isinstance(v, int):
                    vals.append(int(v))
                elif isinstance(v, float):
                    vals.append(float(v))
                else:
                    vals.append(str(v))
            val[rule_k] = vals if len(vals) > 1 else vals[0]

    return [name, params, "recur", val]


CONVERSION_MAP = {
    "geo": lambda prop, params, name: [
        name,
        params,
        "float",
        [prop.latitude, prop.longitude],
    ],
    "request-status": lambda prop, params, name: [
        name,
        params,
        "text",
        prop.split(";"),
    ],
    "binary": lambda prop, params, name: [name, params, "binary", prop],
    "boolean": lambda prop, params, name: [
        name,
        params,
        "boolean",
        prop.to_ical() == b"TRUE",
    ],
    "categories": lambda prop, params, name: [
        name,
        params,
        "text",
        *[str(c) for c in prop.cats],
    ],
    "cal-address": lambda prop, params, name: [name, params, "cal-address", str(prop)],
    "date": date_to_jcal,
    "date-time": datetime_to_jcal,
    "duration": duration_to_jcal,
    "float": float_to_jcal,
    "integer": integer_to_jcal,
    "period": period_to_jcal,
    "recur": recur_to_jcal,
    "text": lambda prop, params, name: [name, params, "text", str(prop)],
    "time": time_to_jcal,
    "uri": lambda prop, params, name: [name, params, "uri", str(prop)],
    "utc-offset": utc_offset_to_jcal,
    "unknown": lambda prop, params, name: [name, params, "unknown", str(prop)],
}

TYPE_TO_VALUE_MAP = {v: k.lower() for k, v in icalendar.cal.types_factory.items()}
TYPE_TO_VALUE_MAP.pop(icalendar.vText, None)

print(TYPE_TO_VALUE_MAP)


def convert_vDDDLists(prop: icalendar.prop.vDDDLists, params: dict, name: str):
    print("Converting vDDDLists", prop)
    results = []
    for dt in prop.dts:
        for r in ical_property_to_jcal("", dt):
            results.append(r)
    print("Results:", results)
    prop_types = set()
    for r in results:
        prop_types.add(r[2])
        params.update(r[1])
    if len(prop_types) > 1:
        print("[Warning] Mixed types in vDDDLists:", prop_types)
    prop_type = list(prop_types)[0]
    val = [r[3] for r in results]  # if len(results) > 1 else results[0][3]
    return [name, params, prop_type, *val]


def ical_property_to_jcal(name: str, prop):
    name = name.lower()
    params: dict[str, str] = getattr(prop, "params", {})
    params = {k.lower(): v for k, v in params.items()}
    value = params.pop("value", "").lower()
    if not value:
        if isinstance(prop, icalendar.vDDDTypes):
            if isinstance(prop.dt, datetime):
                value = "date-time"
            elif isinstance(prop.dt, date):
                value = "date"
            elif isinstance(prop.dt, time):
                value = "time"
            elif isinstance(prop.dt, tuple):
                value = "period"
                prop = icalendar.vPeriod(prop.dt)
        elif name in CONVERSION_MAP:
            value = name
        elif v := TYPE_TO_VALUE_MAP.get(type(prop), None):
            value = v.lower()
        elif v := icalendar.cal.types_factory.types_map.get(name, None):
            value = v.lower()
        else:
            value = "unknown"
    print(f"Converting {name} ([{type(prop)}] {str(prop)}) to {value}")
    if isinstance(prop, icalendar.prop.vDDDLists):
        yield convert_vDDDLists(prop, params, name)
    elif isinstance(prop, list):
        for p in prop:
            yield from ical_property_to_jcal(name, p)
    else:
        yield CONVERSION_MAP[value](prop, params, name)


def to_jcal(comp: icalendar.Component | list[icalendar.Component]):
    if isinstance(comp, list):
        res = [to_jcal(subcomp) for subcomp in comp]
        if len(res) == 1:
            return res[0]
        return res
    properties = []
    for name, value in comp.items():
        for res in ical_property_to_jcal(name, value):
            properties.append(res)
    return [
        comp.name.lower(),
        properties,
        [to_jcal(subcomp) for subcomp in comp.subcomponents],
    ]


def from_ical(ical: str | icalendar.Component | list[icalendar.Component]):
    if isinstance(ical, str):
        ical = icalendar.Component.from_ical(ical, multiple=True)
    return to_jcal(ical)


def jcal_to_ddtypes(jcal_val, prop_type, params: dict):
    if isinstance(jcal_val, (date, datetime, time, timedelta)):
        return jcal_val
    if prop_type == "date":
        dt = date.fromisoformat(jcal_val)
    elif prop_type in ["date-time", "time"]:
        tzinfo = None
        timezone = params.get("tzid", None)
        if isinstance(timezone, str):
            tzinfo = icalendar.timezone.tzp.timezone(timezone)
        elif timezone is not None:
            tzinfo = timezone
        elif jcal_val.endswith("Z"):
            tzinfo = UTC
            jcal_val.rstrip("Z")
        if prop_type == "time":
            dt = time.fromisoformat(jcal_val)
        elif prop_type == "date-time":
            dt = datetime.fromisoformat(jcal_val)
        if tzinfo:
            dt = icalendar.timezone.tzp.localize(dt, tzinfo)
    elif prop_type == "duration":
        dt = icalendar.vDuration.from_ical(jcal_val)
    elif prop_type == "period":
        if isinstance(jcal_val, str):
            jcal_val = jcal_val.split("/", 1)
        start, end_or_duration = jcal_val
        start_dt = jcal_to_ddtypes(start, "date-time", {})
        try:
            try:
                end_dt = jcal_to_ddtypes(end_or_duration, "date-time", {})
            except ValueError:
                end_dt = jcal_to_ddtypes(end_or_duration, "duration", {})
            dt = (start_dt, end_dt)
        except Exception as e:
            raise ValueError(f"Expected period format, got: {jcal_val}") from e
    elif prop_type == "utc-offset":
        sign = -1 if jcal_val.startswith("-") else 1
        print(f"Converting {jcal_val=} to {prop_type=} ({sign=})")
        parts = jcal_val.lstrip("+-").split(":")
        hours, minutes = (int(parts[0]), int(parts[1]))
        if len(parts) > 2:
            seconds = int(parts[2])
        else:
            seconds = 0
        dt = timedelta(hours=hours, minutes=minutes, seconds=seconds) * sign
    print(f"Converted {jcal_val=} to {dt} for {prop_type=}")
    return dt


def jcal_to_recur(jcal_val: dict, prop_type, params: dict):
    val = {}
    for rule_k, rule_v in jcal_val.items():
        rule_k = rule_k.lower()
        if rule_k in ["freq", "wkst"]:
            val[rule_k] = str(rule_v)
        elif rule_k in ["interval", "count"]:
            val[rule_k] = int(rule_v)
        elif rule_k in ["until"]:
            try:
                val[rule_k] = jcal_to_ddtypes(rule_v, "date", {})
            except ValueError:
                val[rule_k] = jcal_to_ddtypes(rule_v, "date-time", {})
        else:
            val[rule_k] = rule_v
    return icalendar.vRecur(**val)


VALUE_TO_TYPE_MAP = {
    icalendar.vDDDTypes: jcal_to_ddtypes,
    icalendar.vPeriod: jcal_to_ddtypes,
    icalendar.vRecur: jcal_to_recur,
    icalendar.vTime: jcal_to_ddtypes,
    icalendar.vDate: jcal_to_ddtypes,
    icalendar.vDatetime: jcal_to_ddtypes,
    icalendar.vDuration: jcal_to_ddtypes,
    icalendar.vUTCOffset: jcal_to_ddtypes,
    icalendar.vGeo: lambda val, _, __: val,
}


def from_jcal(jcal: list | str):
    if isinstance(jcal, str):
        jcal = json.loads(jcal)
    if not isinstance(jcal, list):
        raise ValueError("Invalid jCal format")
    if not jcal:
        raise ValueError("Empty jCal")
    if isinstance(jcal[0], list):
        return [from_jcal(subjcal) for subjcal in jcal]
    if not len(jcal) == 3:
        raise ValueError("Invalid jCal format (Component must have 3 elements)")
    c_name, properties, subcomponents = jcal
    c_class = icalendar.cal.component_factory.get(c_name, icalendar.Component)
    print(f"Creating {c_class.__name__} component {c_name}")
    component: icalendar.Component = c_class()
    if not getattr(component, "name", None):
        component.name = c_name
    for prop in properties:
        p_name, params, value_type, value = (prop[0], prop[1], prop[2], prop[3])
        print(f"Adding property {p_name=} ({value_type=}) with {value=} and {params=}")
        p_name_type = icalendar.cal.types_factory.types_map.get(p_name, None)
        if p_name_type == "geo" and value_type == "float":
            # Special case for geo properties the value type if float
            # but we should parse it as geo
            value_type = "geo"
        if p_name_type == "request-status" and value_type == "text":
            # Special case for request-status properties the value type if text
            # but we should parse it as request-status
            value_type = "request-status"
        if value_type != "unknown" and p_name_type != value_type:
            print(
                f"{p_name_type=} != {value_type=} setting params['value']={value_type}"
            )
            params.update({"value": value_type.upper()})
        p_class = icalendar.cal.types_factory.get(value_type, icalendar.prop.vText)
        print(f"Using {p_class.__name__} for {p_name}")
        if p_class in VALUE_TO_TYPE_MAP:
            value = VALUE_TO_TYPE_MAP[p_class](value, value_type, params)
            value = p_class(value)
            if not hasattr(prop, "params"):
                value.params = icalendar.Parameters()
        if isinstance(value, str):
            value = icalendar.parser.escape_char(value)
        component.add(name=p_name, value=value, parameters=params)
    for subcomp in subcomponents:
        component.add_component(from_jcal(subcomp))
    return component
