from .views.models import Artist, City


def test_create():
    City.objects.create(name="Dnipro")


def test_get_or_create():
    Artist.objects.get_or_create(id="1", defaults={"name": "The Doors"})
    Artist.objects.get_or_create(id="1", defaults={"name": "The Doors"})


def test_update_or_create():
    Artist.objects.update_or_create(id="1", defaults={"name": "The Doors"})
    Artist.objects.update_or_create(id="1", defaults={"name": "The Doors"})
