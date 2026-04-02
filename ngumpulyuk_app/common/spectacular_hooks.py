"""
Satukan skema JWT di OpenAPI: SimpleJWT menambah 'jwtAuth', settings menambah 'BearerAuth'.
Swagger UI mengirim token per *nama skema* — kalau user isi BearerAuth saja, endpoint yang
memakai jwtAuth tidak dapat header Authorization.

Hook ini mengganti semua referensi jwtAuth → BearerAuth dan menghapus definisi jwtAuth.
"""


def use_bearer_auth_only(result, generator, request, public):
    paths = result.get("paths") or {}
    http_ops = frozenset({"get", "put", "post", "delete", "patch", "head", "options", "trace"})

    for path_item in paths.values():
        if not isinstance(path_item, dict):
            continue
        for method, operation in path_item.items():
            if method not in http_ops or not isinstance(operation, dict):
                continue
            sec = operation.get("security")
            if not sec:
                continue
            new_sec = []
            for block in sec:
                if not isinstance(block, dict):
                    new_sec.append(block)
                    continue
                if "jwtAuth" in block:
                    nb = {k: v for k, v in block.items() if k != "jwtAuth"}
                    nb["BearerAuth"] = block["jwtAuth"]
                    new_sec.append(nb)
                else:
                    new_sec.append(block)
            operation["security"] = new_sec

    schemes = result.setdefault("components", {}).setdefault("securitySchemes", {})
    if isinstance(schemes, dict) and "jwtAuth" in schemes:
        del schemes["jwtAuth"]

    return result
