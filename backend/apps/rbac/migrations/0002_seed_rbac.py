"""Seed the default permission catalog, system roles, and their mappings."""
from django.db import migrations


def seed(apps, schema_editor):
    from apps.rbac.constants import (
        PERMISSIONS,
        ROLE_DESCRIPTIONS,
        ROLE_PERMISSIONS,
    )

    Permission = apps.get_model("rbac", "Permission")
    Role = apps.get_model("rbac", "Role")

    perms: dict[str, object] = {}
    for code, name in PERMISSIONS:
        perm, _ = Permission.objects.get_or_create(code=code, defaults={"name": name})
        if perm.name != name:
            perm.name = name
            perm.save(update_fields=["name"])
        perms[code] = perm

    for role_name, codes in ROLE_PERMISSIONS.items():
        role, _ = Role.objects.get_or_create(
            name=role_name,
            defaults={"is_system": True, "description": ROLE_DESCRIPTIONS.get(role_name, "")},
        )
        role.is_system = True
        role.description = ROLE_DESCRIPTIONS.get(role_name, role.description)
        role.save(update_fields=["is_system", "description"])
        role.permissions.set([perms[c] for c in codes])


def unseed(apps, schema_editor):
    from apps.rbac.constants import ROLE_PERMISSIONS

    Role = apps.get_model("rbac", "Role")
    Permission = apps.get_model("rbac", "Permission")
    Role.objects.filter(name__in=list(ROLE_PERMISSIONS.keys())).delete()
    Permission.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [("rbac", "0001_initial")]

    operations = [migrations.RunPython(seed, unseed)]
