from django.db import migrations

def generate_transaction_ids(apps, schema_editor):
    Reservation = apps.get_model('core', 'Reservation')
    counter = 1000
    for reservation in Reservation.objects.all():
        if not reservation.transaction_id:
            reservation.transaction_id = str(counter)
            counter += 1
            reservation.save()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_reservation_transaction_id_alter_item_created_at_and_more'),  # adjust if needed
    ]

    operations = [
        migrations.RunPython(generate_transaction_ids),
    ]
