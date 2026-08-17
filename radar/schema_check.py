from __future__ import annotations
def validate(value: object, schema: dict[str,object]) -> None:
    kinds={"object":dict,"array":list,"string":str,"number":(int,float),"boolean":bool}
    kind=schema.get("type")
    if kind and not isinstance(value,kinds[kind]): raise ValueError(f"expected {kind}")
    if "enum" in schema and value not in schema["enum"]: raise ValueError("not an allowed value")
    if isinstance(value,dict):
        for key in schema.get("required",[]):
            if key not in value: raise ValueError(f"missing {key}")
        for key,child in schema.get("properties",{}).items():
            if key in value: validate(value[key],child)
    if isinstance(value,list) and "items" in schema:
        for item in value: validate(item,schema["items"])
