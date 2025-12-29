from rest_framework import serializers
from decimal import Decimal
from .models import (
    User,
    UserProfile,
    Product, 
    Inventory, 
    Category, 
    SubCategory, 
    Source,
    NewStock,
    Customer,
    Invoice,
    Purchase,
    Transaction,
    ActivityLog
)

class UserSerializer(serializers.ModelSerializer):
    # Make password write-only so it won't be exposed in API responses
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'password']

    def create(self, validated_data):
        # Pop the password and create user with hashed password
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        # Handle password update correctly
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['profileId', 'user', 'qrCodeImage', 'businessName', 'businessAddress', 'businessPhone', 'businessEmail', 'taxId', 'updatedAt']

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['categoryId', 'name', 'createdAt']
        
class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = ['subcategoryId', 'category', 'name', 'createdAt']

class SourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Source
        fields = ['sourceId', 'name', 'sourceUrl', 'contactPerson', 'phone', 'email', 'address', 'createdAt']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['productId', 'productName', 'description', 'image', 'skuCode', 'unit', 'costPrice', 'salePrice', 'discount', 'status', 'subcategory', 'source', 'createdAt']
    
    def to_representation(self, instance):
        """Hide costPrice from staff users"""
        representation = super().to_representation(instance)
        request = self.context.get('request')
        
        # Hide cost price from staff users
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            if request.user.role == 'staff':
                representation.pop('costPrice', None)
        
        return representation

class InventorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Inventory
        fields = ['inventoryId', 'product', 'quantity', 'reorderLevel', 'location', 'updatedAt']

class NewStockSerializer(serializers.ModelSerializer):
    productName = serializers.SerializerMethodField()
    productSku = serializers.SerializerMethodField()
    supplierName = serializers.SerializerMethodField()
    userName = serializers.SerializerMethodField()
    
    class Meta:
        model = NewStock
        fields = ['newstockId', 'inventory', 'quantity', 'purchasePrice', 'receivedDate', 
                  'supplier', 'addedByUser', 'note', 'createdAt', 'productName', 'productSku', 
                  'supplierName', 'userName']
    
    def get_productName(self, obj):
        return obj.inventory.product.productName if obj.inventory and obj.inventory.product else None
    
    def get_productSku(self, obj):
        return obj.inventory.product.skuCode if obj.inventory and obj.inventory.product else None
    
    def get_supplierName(self, obj):
        return obj.supplier.name if obj.supplier else None
    
    def get_userName(self, obj):
        return obj.addedByUser.username if obj.addedByUser else None

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ['customerId', 'name', 'businessAddress', 'phone', 'email', 'customerType', 'firstPurchaseDate', 'createdAt']

class PurchaseNestedSerializer(serializers.ModelSerializer):
    class Meta:
        model = Purchase
        fields = ['product', 'quantity', 'pricePerUnit', 'discount']

class PurchaseReadSerializer(serializers.ModelSerializer):
    """Serializer for reading purchase details with product name"""
    productName = serializers.CharField(source='product.productName', read_only=True)
    
    class Meta:
        model = Purchase
        fields = ['purchaseId', 'product', 'productName', 'quantity', 'pricePerUnit', 'discount', 'subtotal']

class InvoiceSerializer(serializers.ModelSerializer):
    # Allow submitting purchases together
    lineItems = PurchaseNestedSerializer(many=True, write_only=True)
    
    # Tax percentage input (user enters percentage like 10 for 10%)
    taxPercentage = serializers.DecimalField(max_digits=5, decimal_places=2, write_only=True, required=False, default=Decimal('0.00'))
    
    # Make totals read-only so they are calculated in backend
    totalBeforeDiscount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    tax = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)  # Calculated from taxPercentage
    grandTotal = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    
    # Read-only fields for displaying names
    createdByUsername = serializers.CharField(source='createdByUser.username', read_only=True)
    purchases = PurchaseReadSerializer(many=True, read_only=True)

    class Meta:
        model = Invoice
        fields = [
            'invoiceId', 'customer', 'customerName', 'customerPhone', 'createdByUser', 'createdByUsername',
            'paymentMethod', 'note', 'status', 'createdAt', 'paidAt',
            'lineItems', 'purchases', 'taxPercentage', 'totalBeforeDiscount', 'discount', 'tax', 'grandTotal'
        ]
        read_only_fields = ['invoiceId', 'createdByUser', 'createdAt', 'paidAt']

    def create(self, validated_data):
        line_items_data = validated_data.pop('lineItems')
        
        # Validate inventory availability BEFORE creating invoice
        for item_data in line_items_data:
            try:
                inventory = Inventory.objects.get(product=item_data['product'])
                if inventory.quantity < item_data['quantity']:
                    raise serializers.ValidationError({
                        'lineItems': f"Insufficient stock for {item_data['product'].productName}. "
                                   f"Available: {inventory.quantity}, Requested: {item_data['quantity']}"
                    })
            except Inventory.DoesNotExist:
                raise serializers.ValidationError({
                    'lineItems': f"No inventory record found for product: {item_data['product'].productName}"
                })
        
        # Calculate totals before creating invoice
        total_before_discount = Decimal('0.00')
        total_discount = Decimal('0.00')

        for item_data in line_items_data:
            subtotal = item_data['pricePerUnit'] * item_data['quantity']
            total_before_discount += subtotal
            total_discount += item_data.get('discount', Decimal('0.00'))

        # Get tax percentage from user input (or default to 0.00 if not provided)
        tax_percentage = validated_data.pop('taxPercentage', Decimal('0.00'))
        
        # Calculate tax amount from percentage
        # Example: if taxPercentage = 10, then tax = total_before_discount * 0.10
        tax_amount = total_before_discount * (tax_percentage / Decimal('100.00'))
        
        # Add calculated values to validated_data
        validated_data['totalBeforeDiscount'] = total_before_discount
        validated_data['discount'] = total_discount
        validated_data['tax'] = tax_amount  # Calculated from percentage
        validated_data['grandTotal'] = total_before_discount + tax_amount - total_discount
        
        # Now create the invoice with all required fields
        invoice = Invoice.objects.create(**validated_data)

        # Create purchase line items
        # NOTE: Inventory reduction is handled by the signal in signals.py
        for item_data in line_items_data:
            subtotal = item_data['pricePerUnit'] * item_data['quantity']
            subtotal -= item_data.get('discount', Decimal('0.00'))

            Purchase.objects.create(
                invoice=invoice,
                subtotal=subtotal,
                **item_data
            )

        return invoice

class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ['transactionId', 'invoice', 'customer', 'amountPaid', 'paymentMethod', 'transactionStatus', 'paymentReference', 'transactionDate', 'recordedByUser']

class ActivityLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = ActivityLog
        fields = ['logId', 'user', 'username', 'actionType', 'description', 'createdAt']