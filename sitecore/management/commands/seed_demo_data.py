from decimal import Decimal
from datetime import datetime, timezone

from django.core.management.base import BaseCommand

from accounts.models import AdminAccount, User
from catalog.models import Category, Product, SellerProduct
from reservations.models import Reservation
from sitecore.models import PlatformSettings


PRODUCTS = [
    {'id': 'p1', 'name': 'HP LaserJet Pro M404dn', 'price': '450', 'stock': 18, 'brand': 'HP', 'category_id': 'c1', 'image_url': 'https://images.unsplash.com/photo-1628167343682-1f6d7b2e1b5d?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-01-10T00:00:00Z'},
    {'id': 'p2', 'name': 'Canon PIXMA G6020', 'price': '320', 'stock': 12, 'brand': 'Canon', 'category_id': 'c1', 'image_url': 'https://images.unsplash.com/photo-1585792180666-f7347c490ee2?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-01-14T00:00:00Z'},
    {'id': 'p3', 'name': 'Epson EcoTank ET-2850', 'price': '360', 'stock': 7, 'brand': 'Epson', 'category_id': 'c1', 'image_url': 'https://images.unsplash.com/photo-1553413077-190dd305871c?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-01-17T00:00:00Z'},
    {'id': 'p4', 'name': 'Brother HL-L2370DW', 'price': '290', 'stock': 5, 'brand': 'Brother', 'category_id': 'c1', 'image_url': 'https://images.unsplash.com/photo-1517048676732-d65bc937f952?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-01-22T00:00:00Z'},
    {'id': 'p5', 'name': 'Xerox B225 Multifunction', 'price': '399', 'stock': 9, 'brand': 'Xerox', 'category_id': 'c1', 'image_url': 'https://images.unsplash.com/photo-1582582429416-f365cae7a7cd?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-01-24T00:00:00Z'},
    {'id': 'p6', 'name': 'Logitech MX Master Scanner Pack', 'price': '199', 'stock': 4, 'brand': 'Logitech', 'category_id': 'c2', 'image_url': 'https://images.unsplash.com/photo-1587302912306-cf1ed9c33146?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-01-28T00:00:00Z'},
    {'id': 'p7', 'name': 'Premium Toner Cartridge TK-1170', 'price': '75', 'stock': 43, 'brand': 'Kyocera', 'category_id': 'c2', 'image_url': 'https://images.unsplash.com/photo-1516542076529-1ea3854896c4?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-02-01T00:00:00Z'},
    {'id': 'p8', 'name': 'A4 Thermal Label Roll x10', 'price': '42', 'stock': 31, 'brand': 'PrintFlex', 'category_id': 'c2', 'image_url': 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-02-04T00:00:00Z'},
    {'id': 'p9', 'name': 'Industrial Ink Kit C/M/Y/K', 'price': '125', 'stock': 13, 'brand': 'Canon', 'category_id': 'c2', 'image_url': 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-02-08T00:00:00Z'},
    {'id': 'p10', 'name': 'HP OfficeJet Pro 9015e', 'price': '389', 'stock': 3, 'brand': 'HP', 'category_id': 'c1', 'image_url': 'https://images.unsplash.com/photo-1565814329452-e1efa11c5b89?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-02-12T00:00:00Z'},
    {'id': 'p11', 'name': 'Brother MFC-L2750DW', 'price': '410', 'stock': 6, 'brand': 'Brother', 'category_id': 'c1', 'image_url': 'https://images.unsplash.com/photo-1527871369852-eb58cb2bcd89?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-02-14T00:00:00Z'},
    {'id': 'p12', 'name': 'Wireless Print Server Hub', 'price': '149', 'stock': 16, 'brand': 'NetPrint', 'category_id': 'c2', 'image_url': 'https://images.unsplash.com/photo-1517336714731-489689fd1ca8?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-02-18T00:00:00Z'},
    {'id': 'p13', 'name': 'Epson WorkForce WF-2930', 'price': '270', 'stock': 2, 'brand': 'Epson', 'category_id': 'c1', 'image_url': 'https://images.unsplash.com/photo-1588508065123-287b28e013da?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-02-22T00:00:00Z'},
    {'id': 'p14', 'name': 'Auto Duplexer Upgrade Module', 'price': '95', 'stock': 20, 'brand': 'PrintFlex', 'category_id': 'c2', 'image_url': 'https://images.unsplash.com/photo-1516321497487-e288fb19713f?auto=format&fit=crop&w=900&q=80', 'created_at': '2026-02-25T00:00:00Z'},
]

CATEGORIES = [
    {'id': 'c1', 'name': 'Printers'},
    {'id': 'c2', 'name': 'Accessories'},
]

SELLERS = [
    {'id': 's1', 'name': 'Core Retail Hub', 'email': 'seller@test.com', 'business_name': 'Core Retail Hub', 'password': '123456', 'status': User.SellerStatus.APPROVED, 'joined_at': '2026-01-02T00:00:00Z'},
    {'id': 's2', 'name': 'Al Noor Supplies', 'email': 'alnoor@example.com', 'business_name': 'Al Noor Supplies', 'password': 'pass123', 'status': User.SellerStatus.APPROVED, 'joined_at': '2026-01-16T00:00:00Z'},
    {'id': 's3', 'name': 'Tech Station', 'email': 'techstation@example.com', 'business_name': 'Tech Station', 'password': 'pass123', 'status': User.SellerStatus.PENDING, 'joined_at': '2026-03-02T00:00:00Z'},
]

RESERVATIONS = [
    {'id': 'r1', 'product_id': 'p2', 'product_name': 'Canon PIXMA G6020', 'seller_id': 's1', 'seller_name': 'Core Retail Hub', 'quantity': 2, 'base_total': '640', 'final_total': '576', 'status': Reservation.Status.DELIVERED, 'created_at': '2026-03-09T10:20:00Z', 'delivered_at': '2026-03-10T08:15:00Z'},
    {'id': 'r2', 'product_id': 'p8', 'product_name': 'A4 Thermal Label Roll x10', 'seller_id': 's2', 'seller_name': 'Al Noor Supplies', 'quantity': 6, 'base_total': '252', 'final_total': '226.8', 'status': Reservation.Status.PENDING, 'created_at': '2026-03-11T14:15:00Z'},
    {'id': 'r3', 'product_id': 'p10', 'product_name': 'HP OfficeJet Pro 9015e', 'seller_id': 's2', 'seller_name': 'Al Noor Supplies', 'quantity': 1, 'base_total': '389', 'final_total': '350.1', 'status': Reservation.Status.APPROVED, 'created_at': '2026-04-02T09:05:00Z'},
    {'id': 'r4', 'product_id': 'p13', 'product_name': 'Epson WorkForce WF-2930', 'seller_id': 's1', 'seller_name': 'Core Retail Hub', 'quantity': 2, 'base_total': '540', 'final_total': '486', 'status': Reservation.Status.REJECTED, 'created_at': '2026-04-05T13:40:00Z', 'removed_at': '2026-04-05T15:05:00Z'},
    {'id': 'r5', 'product_id': 'p7', 'product_name': 'Premium Toner Cartridge TK-1170', 'seller_id': 's3', 'seller_name': 'Tech Station', 'quantity': 8, 'base_total': '600', 'final_total': '540', 'status': Reservation.Status.DELIVERED, 'created_at': '2026-04-08T10:25:00Z', 'delivered_at': '2026-04-09T08:45:00Z'},
]


class Command(BaseCommand):
    help = 'Seed demo data for the DIPCOM frontend.'

    def handle(self, *args, **options):
        settings = PlatformSettings.get_solo()
        settings.commission_percent = Decimal('10')
        settings.contact_phone = '+1 (555) 900-1001'
        settings.contact_address = 'Next to CBE Temenja Yaj branch, Kirkos sub city woreda 11, Addis Ababa'
        settings.business_hours = 'Monday - Saturday, 8:30 AM - 6:00 PM'
        settings.tiktok_url = 'https://www.tiktok.com/@dipcomtechnologies'
        settings.map_url = 'https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d3940.728265867298!2d38.75657401086354!3d8.99713269102569!2m3!1f0!2f0!3f0!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x164b8584482eab63%3A0x2c55bad0b8eff98a!2sDipcom%20Technology%20Solutions!5e0!3m2!1sen!2set!4v1775917748282!5m2!1sen!2set'
        settings.hero_tagline = 'Stock Management & Reseller System'
        settings.hero_title = 'Import printers, repair devices, and train teams with a premium business platform.'
        settings.hero_description = 'This public landing page introduces the full service story behind the system: printer imports, repairs, training, and a modern reseller experience.'
        settings.about_title = '18 years of trusted printer importing, repair, and training expertise.'
        settings.about_description = 'DIPCOM Technologies is a seasoned service provider with more than 18 years of experience in printer importing, printer repair, and practical training.'
        settings.years_experience = 18
        settings.students_trained = 200
        settings.save()

        category_lookup = {}
        for category in CATEGORIES:
            obj, _ = Category.objects.update_or_create(
                id=category['id'],
                defaults={
                    'name': category['name'],
                    'created_by': User.objects.filter(role=User.Role.ADMIN).first(),
                },
            )
            category_lookup[category['id']] = obj

        for name, email, role in [
            ('Platform Admin', 'admin@test.com', User.Role.ADMIN),
            ('Reservations Staff', 'staff@test.com', User.Role.STAFF),
            ('Core Retail Hub', 'seller@test.com', User.Role.SELLER),
        ]:
            user, _ = User.objects.get_or_create(email=email, defaults={'display_name': name, 'role': role, 'seller_status': User.SellerStatus.APPROVED if role != User.Role.SELLER else User.SellerStatus.APPROVED, 'business_name': name if role == User.Role.SELLER else ''})
            user.display_name = name
            user.role = role
            user.business_name = name if role == User.Role.SELLER else ''
            user.seller_status = User.SellerStatus.APPROVED if role != User.Role.SELLER else User.SellerStatus.APPROVED
            user.is_staff = role in {User.Role.ADMIN, User.Role.STAFF}
            user.is_superuser = role == User.Role.ADMIN
            user.set_password('123456')
            user.save()

        seller_lookup = {}
        for seller in SELLERS:
            user, _ = User.objects.get_or_create(email=seller['email'], defaults={'display_name': seller['name'], 'business_name': seller['business_name'], 'role': User.Role.SELLER, 'seller_status': seller['status']})
            user.display_name = seller['name']
            user.business_name = seller['business_name']
            user.role = User.Role.SELLER
            user.seller_status = seller['status']
            user.is_staff = False
            user.is_superuser = False
            user.set_password(seller['password'])
            user.save()
            seller_lookup[seller['id']] = user

        admin_accounts = [
            ('Platform Admin', 'admin@test.com', 'Super Admin', '2026-01-01T00:00:00Z'),
            ('Operations Lead', 'ops@dipcomtechnologies.com', 'Operations Admin', '2026-01-18T00:00:00Z'),
        ]
        for name, email, role, joined_at in admin_accounts:
            AdminAccount.objects.update_or_create(
                email=email,
                defaults={'name': name, 'role': role, 'joined_at': datetime.fromisoformat(joined_at.replace('Z', '+00:00'))},
            )

        product_lookup = {}
        for item in PRODUCTS:
            created_at = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
            product, _ = Product.objects.update_or_create(
                id=item['id'],
                defaults={
                    'name': item['name'],
                    'price': item['price'],
                    'stock': item['stock'],
                    'brand': item['brand'],
                    'category': category_lookup[item['category_id']],
                    'image_url': item['image_url'],
                    'created_by': User.objects.filter(role=User.Role.ADMIN).first(),
                },
            )
            Product.objects.filter(id=product.id).update(created_at=created_at, updated_at=created_at)
            product_lookup[item['id']] = product

        seller_products = [
            {'id': 'sp1', 'seller_id': 's1', 'name': 'Core Label Tape Pack', 'price': '38', 'stock': 42, 'brand': 'Core Retail Hub', 'category_id': 'c2', 'image_url': 'https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80'},
            {'id': 'sp2', 'seller_id': 's1', 'name': 'Office Ink Multi Kit', 'price': '112', 'stock': 8, 'brand': 'Core Retail Hub', 'category_id': 'c2', 'image_url': 'https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=900&q=80'},
            {'id': 'sp3', 'seller_id': 's1', 'name': 'Compact Receipt Printer', 'price': '178', 'stock': 3, 'brand': 'Core Retail Hub', 'category_id': 'c1', 'image_url': 'https://images.unsplash.com/photo-1628167343682-1f6d7b2e1b5d?auto=format&fit=crop&w=900&q=80'},
            {'id': 'sp4', 'seller_id': 's2', 'name': 'Al Noor Barcode Stickers', 'price': '46', 'stock': 18, 'brand': 'Al Noor Supplies', 'category_id': 'c2', 'image_url': 'https://images.unsplash.com/photo-1516542076529-1ea3854896c4?auto=format&fit=crop&w=900&q=80'},
        ]
        for item in seller_products:
            created_at_raw = item.get('created_at')
            created_at = (
                datetime.fromisoformat(created_at_raw.replace('Z', '+00:00'))
                if created_at_raw
                else datetime.now(timezone.utc)
            )
            SellerProduct.objects.update_or_create(
                id=item['id'],
                defaults={
                    'seller': seller_lookup[item['seller_id']],
                    'name': item['name'],
                    'price': item['price'],
                    'stock': item['stock'],
                    'brand': item['brand'],
                    'category': category_lookup[item['category_id']],
                    'image_url': item['image_url'],
                },
            )
            SellerProduct.objects.filter(id=item['id']).update(created_at=created_at, updated_at=created_at)

        for item in RESERVATIONS:
            created_at = datetime.fromisoformat(item['created_at'].replace('Z', '+00:00'))
            delivered_at = datetime.fromisoformat(item['delivered_at'].replace('Z', '+00:00')) if item.get('delivered_at') else None
            removed_at = datetime.fromisoformat(item['removed_at'].replace('Z', '+00:00')) if item.get('removed_at') else None
            Reservation.objects.update_or_create(
                id=item['id'],
                defaults={
                    'product': product_lookup[item['product_id']],
                    'seller': seller_lookup[item['seller_id']],
                    'product_name': item['product_name'],
                    'seller_name': item['seller_name'],
                    'quantity': item['quantity'],
                    'base_total': item['base_total'],
                    'final_total': item['final_total'],
                    'status': item['status'],
                },
            )
            Reservation.objects.filter(id=item['id']).update(
                created_at=created_at,
                delivered_at=delivered_at,
                removed_at=removed_at,
            )

        self.stdout.write(self.style.SUCCESS('Demo data seeded successfully.'))