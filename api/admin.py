from django.contrib import admin
from .models import (
    User, UserProfile, Category, SubCategory, Source, Product, Inventory, NewStock,
    Customer, Invoice, Purchase, Transaction, ActivityLog
)

from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

# ------------------- User -------------------
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'date_joined')
    list_filter = ('role', 'is_superuser', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Custom Fields', {'fields': ('role',)}),
    )

# ------------------- UserProfile -------------------
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'businessName', 'businessPhone', 'updatedAt')
    search_fields = ('user__username', 'businessName')

# ------------------- Category -------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'createdAt')
    search_fields = ('name',)

# ------------------- SubCategory -------------------
@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'createdAt')
    list_filter = ('category',)
    search_fields = ('name', 'category__name')

# ------------------- Source -------------------
@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ('name', 'contactPerson', 'phone', 'email')
    search_fields = ('name', 'contactPerson', 'email')

# ------------------- Product -------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('productName', 'skuCode', 'subcategory', 'status', 'unit')
    list_filter = ('status', 'subcategory__category', 'subcategory')
    search_fields = ('productName', 'skuCode')
    ordering = ('productName',)
    fieldsets = (
        (None, {
            'fields': ('productName', 'skuCode', 'description', 'image')
        }),
        ('Categorization', {
            'fields': ('subcategory', 'source', 'status', 'unit')
        }),
    )
    # Enable autocomplete for this model to be used in other admins
    # This is used by InventoryAdmin, PurchaseInline, etc.

# ------------------- Inventory -------------------
@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'location', 'reorderLevel', 'updatedAt')
    list_filter = ('location',)
    search_fields = ('product__productName', 'location')
    autocomplete_fields = ('product',)

# ------------------- NewStock -------------------
@admin.register(NewStock)
class NewStockAdmin(admin.ModelAdmin):
    list_display = ('inventory', 'quantity', 'purchasePrice', 'receivedDate', 'supplier')
    list_filter = ('receivedDate', 'supplier')
    search_fields = ('inventory__product__productName', 'supplier__name')
    autocomplete_fields = ('inventory', 'supplier', 'addedByUser')
    date_hierarchy = 'receivedDate'

# ------------------- Customer -------------------
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'customerType', 'phone', 'email', 'firstPurchaseDate')
    list_filter = ('customerType',)
    search_fields = ('name', 'email', 'phone')

# ------------------- Purchase Inline for Invoice -------------------
class PurchaseInline(admin.TabularInline):
    model = Purchase
    extra = 1
    autocomplete_fields = ('product',)

# ------------------- Invoice -------------------
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoiceId', 'customer', 'grandTotal', 'status', 'createdAt', 'createdByUser')
    list_filter = ('status', 'paymentMethod', 'createdAt')
    search_fields = ('invoiceId', 'customer__name')
    autocomplete_fields = ('customer', 'createdByUser')
    date_hierarchy = 'createdAt'
    inlines = [PurchaseInline]

# ------------------- Purchase -------------------
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('invoice', 'product', 'quantity', 'pricePerUnit', 'subtotal')
    search_fields = ('invoice__invoiceId', 'product__productName')
    autocomplete_fields = ('invoice', 'product')

# ------------------- Transaction -------------------
@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transactionId', 'invoice', 'amountPaid', 'paymentMethod', 'transactionStatus', 'transactionDate')
    list_filter = ('transactionStatus', 'paymentMethod', 'transactionDate')
    search_fields = ('transactionId', 'invoice__invoiceId', 'paymentReference')
    autocomplete_fields = ('invoice', 'customer', 'recordedByUser')
    date_hierarchy = 'transactionDate'

# ------------------- ActivityLog -------------------
@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('actionType', 'user', 'description', 'createdAt')
    list_filter = ('actionType', 'user')
    search_fields = ('description', 'user__username')
    date_hierarchy = 'createdAt'
    readonly_fields = ('createdAt',)
