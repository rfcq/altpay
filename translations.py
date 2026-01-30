# -*- coding: utf-8 -*-
"""Translations for AltPay (en and pt-BR)."""

SUPPORTED_LANGS = ['en', 'pt-BR']

TRANSLATIONS = {
    'en': {
        # Language selection
        'choose_language': 'Choose language',
        'choose_language_subtitle': 'Select your preferred language',
        'lang_en': 'English',
        'lang_pt_BR': 'Português (Brasil)',
        # General
        'app_name': 'AltPay Shop',
        'welcome': 'Welcome, {username}!',
        'logout': 'Logout',
        'sidebar_toggle': 'Open or close menu',
        # Sidebar
        'nav_create_product': 'Create Product',
        'nav_products': 'Products',
        'nav_cart': 'Cart',
        'nav_users': 'Users',
        # Ephemeral DB warning
        'ephemeral_db_msg': 'Data is not persistent on this deployment (no database). Add <code>DATABASE_URL</code> for persistent storage. See VERCEL.md.',
        # Auth
        'login': 'Login',
        'login_title': 'Login - AltPay',
        'username': 'Username',
        'password': 'Password',
        'username_placeholder': 'Username',
        'password_placeholder': 'Password',
        'no_account': "Don't have an account? Contact an administrator to get one.",
        'register': 'Register',
        'register_title': 'Register - AltPay',
        'create_first_admin': 'Create first admin account',
        'add_new_user': 'Add new user',
        'first_user_hint': 'No users exist yet. This account will be the administrator.',
        'email': 'Email',
        'email_placeholder': 'Email',
        'password_min': 'Password (min 6)',
        'confirm_password': 'Confirm Password',
        'confirm_placeholder': 'Confirm',
        'already_account': 'Already have an account?',
        # Create product
        'create_product': 'Create Product',
        'create_product_title': 'Create Product – AltPay Shop',
        'name': 'Name',
        'name_placeholder': 'e.g. Coffee',
        'price': 'Price',
        'price_placeholder': '9.90',
        'add_product': 'Add product',
        'import_from_file': 'Import from file',
        'import_products': 'Import products',
        'import_select_file': 'Select CSV or JSON file',
        'import_btn': 'Import',
        'import_format_hint': 'CSV: header row with name, price. JSON: array of { "name": "...", "price": number } or { "products": [...] }.',
        'import_success': '{count} product(s) imported.',
        'import_no_file': 'No file selected.',
        'import_bad_type': 'File must be CSV or JSON.',
        'import_empty': 'File is empty or invalid.',
        'import_json_format': 'JSON must be an array or object with "products" array.',
        'import_json_invalid': 'Invalid JSON.',
        'import_error': 'Import failed.',
        'import_row_invalid': 'Row {row}: invalid or skipped.',
        # Products
        'products': 'Products',
        'products_title': 'Products – AltPay Shop',
        'select_all': 'Select all',
        'print_selected': 'Print Selected',
        'delete_selected': 'Delete Selected',
        'add_selected_to_cart': 'Add selected to cart',
        'add_to_cart': 'Add to cart',
        'edit': 'Edit',
        'delete': 'Delete',
        'no_products': 'No products yet.',
        'create_one': 'Create one',
        'edit_product': 'Edit Product',
        'save': 'Save',
        'cancel': 'Cancel',
        'print_preview': 'Print Preview',
        'print': 'Print',
        'close': 'Close',
        # Cart
        'cart': 'Cart',
        'cart_title': 'Cart – AltPay Shop',
        'scan_qr': 'Scan QR Code',
        'total': 'Total',
        'print_cart': 'Print Cart',
        'clear_cart': 'Clear Cart',
        'cart_empty': 'Cart is empty. Scan a QR or add from',
        'finish_buy': 'Finish buy',
        'checkout_cart_empty': 'Cart is empty. Add products before finishing.',
        'checkout_success': 'Purchase completed. Products added to Products sold.',
        'checkout_error': 'Checkout failed.',
        'products_sold': 'Products sold',
        'products_sold_title': 'Products sold – AltPay Shop',
        'products_sold_empty': 'No sales yet. Finish a buy from the Cart to see them here.',
        'products_sold_hint': 'List of completed purchases (cart checkout).',
        'sale_date': 'Date',
        'sale_items': 'Items',
        'sale_total': 'Total',
        'scan_qr_modal': 'Scan QR Code',
        'switch_camera': 'Switch camera',
        'point_camera': 'Point camera at QR code...',
        # Users
        'users': 'Users',
        'users_title': 'Users – AltPay Shop',
        'add_user': 'Add user',
        'users_hint': 'Only admins can add new users. New accounts can log in after you create them.',
        'username_col': 'Username',
        'role': 'Role',
        'created': 'Created',
        'role_admin': 'Administrator',
        'role_user': 'User',
        'no_users': 'No users yet.',
        'add_first_user': 'Add the first user (they will be admin).',
        # Flash / API messages (backend)
        'msg_admin_required': 'Admin access required.',
        'msg_only_admins': 'Only admins can add new users.',
        'msg_contact_admin': 'Contact an administrator for an account.',
        'msg_all_required': 'All fields are required.',
        'msg_passwords_dont_match': 'Passwords do not match.',
        'msg_password_min': 'Password must be at least 6 characters.',
        'msg_username_exists': 'Username already exists.',
        'msg_email_registered': 'Email already registered.',
        'msg_registration_success': 'Registration successful! Please login.',
        'msg_user_created': 'User created. They can log in now.',
        'msg_enter_credentials': 'Please enter both username and password.',
        'msg_welcome_back': 'Welcome back, {username}!',
        'msg_invalid_credentials': 'Invalid username or password.',
        'msg_logged_out': 'You have been logged out.',
        'err_invalid_price': 'Invalid price format.',
        'err_invalid_name_price': 'Invalid name or price.',
        'err_product_not_found': 'Product not found.',
        'err_cannot_delete_default': 'Cannot delete default products.',
        'err_invalid_product_ids': 'Invalid product IDs.',
        'err_no_valid_products': 'No valid products to delete.',
        'err_invalid_data': 'Invalid data.',
        'msg_product_deleted': 'Product deleted.',
        'msg_products_deleted': '{n} product(s) deleted.',
        'msg_one_product_deleted': '1 product deleted.',
        'msg_added_to_cart': 'Added to cart.',
        'msg_added_n_to_cart': '{n} product(s) added to cart.',
        'msg_cart_cleared': 'Cart cleared.',
        # Ephemeral (login page)
        'ephemeral_login': 'Data is not persistent on this deployment. Accounts may disappear between visits. Add DATABASE_URL for persistent storage (see VERCEL.md).',
        'currency': '$',
    },
    'pt-BR': {
        'choose_language': 'Escolha o idioma',
        'choose_language_subtitle': 'Selecione seu idioma preferido',
        'lang_en': 'English',
        'lang_pt_BR': 'Português (Brasil)',
        'app_name': 'AltPay Shop',
        'welcome': 'Bem-vindo(a), {username}!',
        'logout': 'Sair',
        'sidebar_toggle': 'Abrir ou fechar menu',
        'nav_create_product': 'Criar produto',
        'nav_products': 'Produtos',
        'nav_cart': 'Carrinho',
        'nav_users': 'Usuários',
        'ephemeral_db_msg': 'Os dados não são persistentes nesta implantação (sem banco). Configure <code>DATABASE_URL</code> para armazenamento persistente. Veja VERCEL.md.',
        'login': 'Entrar',
        'login_title': 'Entrar - AltPay',
        'username': 'Nome de usuário',
        'password': 'Senha',
        'username_placeholder': 'Nome de usuário',
        'password_placeholder': 'Senha',
        'no_account': 'Não tem conta? Entre em contato com um administrador.',
        'register': 'Cadastrar',
        'register_title': 'Cadastrar - AltPay',
        'create_first_admin': 'Criar primeira conta de administrador',
        'add_new_user': 'Adicionar novo usuário',
        'first_user_hint': 'Ainda não há usuários. Esta conta será a administradora.',
        'email': 'E-mail',
        'email_placeholder': 'E-mail',
        'password_min': 'Senha (mín. 6)',
        'confirm_password': 'Confirmar senha',
        'confirm_placeholder': 'Confirmar',
        'already_account': 'Já tem conta?',
        'create_product': 'Criar produto',
        'create_product_title': 'Criar produto – AltPay Shop',
        'name': 'Nome',
        'name_placeholder': 'ex.: Café',
        'price': 'Preço',
        'price_placeholder': '9,90',
        'add_product': 'Adicionar produto',
        'import_from_file': 'Importar de arquivo',
        'import_products': 'Importar produtos',
        'import_select_file': 'Selecione arquivo CSV ou JSON',
        'import_btn': 'Importar',
        'import_format_hint': 'CSV: linha de cabeçalho com name, price. JSON: array de { "name": "...", "price": número } ou { "products": [...] }.',
        'import_success': '{count} produto(s) importado(s).',
        'import_no_file': 'Nenhum arquivo selecionado.',
        'import_bad_type': 'Arquivo deve ser CSV ou JSON.',
        'import_empty': 'Arquivo vazio ou inválido.',
        'import_json_format': 'JSON deve ser um array ou objeto com array "products".',
        'import_json_invalid': 'JSON inválido.',
        'import_error': 'Falha na importação.',
        'import_row_invalid': 'Linha {row}: inválida ou ignorada.',
        'products': 'Produtos',
        'products_title': 'Produtos – AltPay Shop',
        'select_all': 'Selecionar todos',
        'print_selected': 'Imprimir selecionados',
        'delete_selected': 'Excluir selecionados',
        'add_selected_to_cart': 'Adicionar selecionados ao carrinho',
        'add_to_cart': 'Adicionar ao carrinho',
        'edit': 'Editar',
        'delete': 'Excluir',
        'no_products': 'Nenhum produto ainda.',
        'create_one': 'Criar um',
        'edit_product': 'Editar produto',
        'save': 'Salvar',
        'cancel': 'Cancelar',
        'print_preview': 'Visualizar impressão',
        'print': 'Imprimir',
        'close': 'Fechar',
        'cart': 'Carrinho',
        'cart_title': 'Carrinho – AltPay Shop',
        'scan_qr': 'Escanear código QR',
        'total': 'Total',
        'print_cart': 'Imprimir carrinho',
        'clear_cart': 'Limpar carrinho',
        'cart_empty': 'Carrinho vazio. Escaneie um QR ou adicione em',
        'finish_buy': 'Finalizar compra',
        'checkout_cart_empty': 'Carrinho vazio. Adicione produtos antes de finalizar.',
        'checkout_success': 'Compra concluída. Produtos adicionados em Produtos vendidos.',
        'checkout_error': 'Falha ao finalizar compra.',
        'products_sold': 'Produtos vendidos',
        'products_sold_title': 'Produtos vendidos – AltPay Shop',
        'products_sold_empty': 'Nenhuma venda ainda. Finalize uma compra no Carrinho para ver aqui.',
        'products_sold_hint': 'Lista de compras finalizadas (checkout do carrinho).',
        'sale_date': 'Data',
        'sale_items': 'Itens',
        'sale_total': 'Total',
        'scan_qr_modal': 'Escanear código QR',
        'switch_camera': 'Trocar câmera',
        'point_camera': 'Aponte a câmera para o código QR...',
        'users': 'Usuários',
        'users_title': 'Usuários – AltPay Shop',
        'add_user': 'Adicionar usuário',
        'users_hint': 'Apenas administradores podem adicionar usuários. Novas contas podem entrar após você criá-las.',
        'username_col': 'Nome de usuário',
        'role': 'Função',
        'created': 'Criado em',
        'role_admin': 'Administrador',
        'role_user': 'Usuário',
        'no_users': 'Nenhum usuário ainda.',
        'add_first_user': 'Adicione o primeiro (será administrador).',
        'msg_admin_required': 'Acesso restrito a administradores.',
        'msg_only_admins': 'Apenas administradores podem adicionar usuários.',
        'msg_contact_admin': 'Entre em contato com um administrador para obter uma conta.',
        'msg_all_required': 'Todos os campos são obrigatórios.',
        'msg_passwords_dont_match': 'As senhas não coincidem.',
        'msg_password_min': 'A senha deve ter no mínimo 6 caracteres.',
        'msg_username_exists': 'Nome de usuário já existe.',
        'msg_email_registered': 'E-mail já cadastrado.',
        'msg_registration_success': 'Cadastro realizado! Faça login.',
        'msg_user_created': 'Usuário criado. Ele já pode entrar.',
        'msg_enter_credentials': 'Informe nome de usuário e senha.',
        'msg_welcome_back': 'Bem-vindo(a) de volta, {username}!',
        'msg_invalid_credentials': 'Nome de usuário ou senha inválidos.',
        'msg_logged_out': 'Você saiu da sua conta.',
        'err_invalid_price': 'Formato de preço inválido.',
        'err_invalid_name_price': 'Nome ou preço inválido.',
        'err_product_not_found': 'Produto não encontrado.',
        'err_cannot_delete_default': 'Não é possível excluir os produtos padrão.',
        'err_invalid_product_ids': 'IDs de produto inválidos.',
        'err_no_valid_products': 'Nenhum produto válido para excluir.',
        'err_invalid_data': 'Dados inválidos.',
        'msg_product_deleted': 'Produto excluído.',
        'msg_products_deleted': '{n} produto(s) excluído(s).',
        'msg_one_product_deleted': '1 produto excluído.',
        'msg_added_to_cart': 'Adicionado ao carrinho.',
        'msg_added_n_to_cart': '{n} produto(s) adicionado(s) ao carrinho.',
        'msg_cart_cleared': 'Carrinho esvaziado.',
        'ephemeral_login': 'Os dados não são persistentes nesta implantação. As contas podem sumir entre acessos. Configure DATABASE_URL para armazenamento persistente (veja VERCEL.md).',
        'currency': 'R$',
    },
}

# Keys used in JavaScript (subset) – same keys, exposed to frontend
JS_KEYS = [
    'err_invalid_price', 'err_invalid_name_price', 'err_product_not_found',
    'err_cannot_delete_default', 'err_invalid_product_ids', 'err_no_valid_products',
    'err_invalid_data', 'msg_product_deleted', 'msg_added_to_cart', 'msg_added_n_to_cart', 'msg_cart_cleared',
    'enter_valid_name_price', 'clear_cart_confirm', 'invalid', 'delete_product_confirm',
    'select_at_least_one', 'delete_products_confirm', 'add_selected_to_cart', 'msg_added_n_to_cart',
    'cart_empty', 'carrinho', 'produtos_selecionados',
    'no_qr', 'items', 'total', 'camera_not_supported', 'requesting_camera', 'point_at_qr',
    'error_starting_camera', 'camera_denied', 'allow_in_settings', 'no_camera_found',
    'trying', 'camera_error', 'processing', 'added', 'failed', 'invalid_qr',
    'currency',
    'checkout_success', 'checkout_cart_empty',
]

# Add JS-only keys that don't exist in TRANSLATIONS
for lang in TRANSLATIONS:
    d = TRANSLATIONS[lang]
    if lang == 'en':
        d['enter_valid_name_price'] = 'Enter valid name and price.'
        d['clear_cart_confirm'] = 'Clear cart?'
        d['invalid'] = 'Invalid.'
        d['delete_product_confirm'] = 'Delete "{name}"?'
        d['select_at_least_one'] = 'Select at least one product.'
        d['delete_products_confirm'] = 'Delete {n} product(s)?'
        d['carrinho'] = 'Cart'
        d['produtos_selecionados'] = 'Selected Products'
        d['no_qr'] = 'No QR'
        d['items'] = 'Items'
        d['total'] = 'Total'
        d['camera_not_supported'] = 'Camera not supported.'
        d['requesting_camera'] = 'Requesting camera...'
        d['point_at_qr'] = 'Point at QR code...'
        d['error_starting_camera'] = 'Error starting camera'
        d['camera_denied'] = 'Camera denied. '
        d['allow_in_settings'] = 'Allow in Settings.'
        d['no_camera_found'] = 'No camera found.'
        d['trying'] = 'Trying...'
        d['camera_error'] = 'Camera error'
        d['processing'] = 'Processing...'
        d['added'] = 'Added'
        d['failed'] = 'Failed'
        d['invalid_qr'] = 'Invalid QR'
    else:
        d['enter_valid_name_price'] = 'Informe nome e preço válidos.'
        d['clear_cart_confirm'] = 'Limpar carrinho?'
        d['invalid'] = 'Inválido.'
        d['delete_product_confirm'] = 'Excluir "{name}"?'
        d['select_at_least_one'] = 'Selecione pelo menos um produto.'
        d['delete_products_confirm'] = 'Excluir {n} produto(s)?'
        d['carrinho'] = 'Carrinho'
        d['produtos_selecionados'] = 'Produtos selecionados'
        d['no_qr'] = 'Sem QR'
        d['items'] = 'Itens'
        d['camera_not_supported'] = 'Câmera não suportada.'
        d['requesting_camera'] = 'Solicitando câmera...'
        d['point_at_qr'] = 'Aponte para o código QR...'
        d['error_starting_camera'] = 'Erro ao iniciar câmera'
        d['camera_denied'] = 'Câmera negada. '
        d['allow_in_settings'] = 'Permita nas configurações.'
        d['no_camera_found'] = 'Nenhuma câmera encontrada.'
        d['trying'] = 'Tentando...'
        d['camera_error'] = 'Erro na câmera'
        d['processing'] = 'Processando...'
        d['added'] = 'Adicionado'
        d['failed'] = 'Falha'
        d['invalid_qr'] = 'QR inválido'
