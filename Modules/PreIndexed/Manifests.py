import hashlib
import yaml


def rest_response_to_manifests(rest_json: dict) -> tuple[str, bytes]:
    data = rest_json.get('Data', rest_json)
    pid = data.get("PackageIdentifier", "Unknown.Unknown")
    manifest_version = "1.12.0"

    versions = data.get("Versions", [])
    v_data = versions[0] if versions else {}
    ver = v_data.get("PackageVersion", "0.0.0")
    locale_data = v_data.get("DefaultLocale", {})

    singleton_manifest = {
        "PackageIdentifier": pid,
        "PackageVersion": ver,
        "PackageName": locale_data.get("PackageName", pid.split('.')[-1]),
        "Publisher": locale_data.get("Publisher", pid.split('.')[0]),
        "PackageLocale": locale_data.get("PackageLocale", "en-US"),
        "ManifestType": "singleton",
        "ManifestVersion": manifest_version,
        "DefaultLocale": locale_data.get("PackageLocale", "en-US"),
    }

    important_keys = [
        "License", "LicenseUrl", "ShortDescription", "Description",
        "PackageUrl", "PublisherUrl", "PublisherSupportUrl", "PrivacyUrl",
        "Copyright", "CopyrightUrl", "Tags", "Moniker"
    ]
    for key in important_keys:
        if key in locale_data:
            singleton_manifest[key] = locale_data[key]

    installers = [_map_installer(i) for i in v_data.get("Installers", [])]
    installers.sort(key=lambda x: (x.get("Architecture", ""), x.get("InstallerType", "")), reverse=True)
    singleton_manifest["Installers"] = installers

    yaml_args = {
        "sort_keys": False,
        "allow_unicode": True,
        "default_flow_style": False,
        "width": 1000
    }

    manifest_content = yaml.dump(singleton_manifest, **yaml_args)
    manifest_bytes = manifest_content.encode('utf-8')
    manifest_hash_bin = hashlib.sha256(manifest_bytes).digest()
    return manifest_content, manifest_hash_bin


def _map_installer(inst: dict) -> dict:
    skip_keys = {"InstallerIdentifier"}
    new_inst = {}

    for k, v in inst.items():
        if k in skip_keys or v is None:
            continue
        if isinstance(v, list) and len(v) == 0:
            continue

        if isinstance(v, dict):
            cleaned_dict = _map_installer(v)
            if cleaned_dict:
                new_inst[k] = cleaned_dict
        elif isinstance(v, list):
            cleaned_list = []
            for item in v:
                if isinstance(item, dict):
                    c_item = _map_installer(item)
                    if c_item: cleaned_list.append(c_item)
                else:
                    cleaned_list.append(item)
            if cleaned_list:
                new_inst[k] = cleaned_list
        else:
            new_inst[k] = v
    return new_inst
