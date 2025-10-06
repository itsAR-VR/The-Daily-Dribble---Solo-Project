#!/usr/bin/env python3
"""
Platform-specific configurations for the multi-platform listing bot.
This centralizes all platform-specific details for easy maintenance.
"""

# Platform configurations with selectors, URLs, and requirements
PLATFORM_CONFIGS = {
    'cellpex': {
        'name': 'Cellpex',
        'base_url': 'https://www.cellpex.com',
        'login': {
            'url': 'https://www.cellpex.com/login',
            'selectors': {
                'username': 'input[name="txtUser"]',
                'password': 'input[name="txtPass"]',
                'submit': 'input[name="btnLogin"]'
            }
        },
        'has_2fa': False,  # To be confirmed
        '2fa_method': None,  # email, sms, or authenticator
        'listing': {
            'urls': [
                'https://www.cellpex.com/seller/products/create',
                'https://www.cellpex.com/post-listing',
                'https://www.cellpex.com/sell'
            ],
            'selectors': {
                'product_name': ['input[name="name"]', 'input[name="product_name"]'],
                'quantity': ['input[name="qty"]', 'input[name="quantity"]'],
                'price': ['input[name="price"]'],
                'condition': ['select[name="condition"]'],
                'description': ['textarea[name="description"]', 'textarea[name="desc"]']
            }
        },
        'success_indicators': ['dashboard', 'my products', 'seller', 'logout'],
        'rate_limit': {
            'listings_per_hour': 20,
            'delay_between_listings': 5  # seconds
        }
    },
    
    'gsmexchange': {
        'name': 'GSM Exchange',
        'base_url': 'https://www.gsmexchange.com',
        'login': {
            'url': 'https://www.gsmexchange.com/signin',
            'selectors': {
                'username': 'input[name="username"]',
                'password': 'input[name="password"]',
                'submit': 'button[type="submit"]'
            }
        },
        'has_2fa': True,
        '2fa_method': 'email',
        'listing': {
            'urls': [
                'https://www.gsmexchange.com/gsm/post_offers.html'
            ],
            'selectors': {
                'listing_type': 'input[value="sell"]',  # Radio button
                'product_name': ['input[name="title"]'],
                'quantity': ['input[name="qty"]'],
                'price': ['input[name="price"]'],
                'condition': ['select[name="condition"]'],
                'description': ['textarea[name="description"]']
            }
        },
        'success_indicators': ['my account', 'post listing', 'dashboard', 'logout'],
        'rate_limit': {
            'listings_per_hour': 30,
            'delay_between_listings': 3
        }
    },
    
    'hubx': {
        'name': 'HubX',
        'base_url': 'https://app.hubx.com',
        'login': {
            'url': 'https://app.hubx.com/login',
            'selectors': {
                'username': 'input[name="email"]',
                'password': 'input[name="password"]',
                'submit': 'button[type="submit"]'
            }
        },
        'has_2fa': None,  # To be tested
        '2fa_method': None,
        'listing': {
            'urls': [
                'https://app.hubx.com/inventory/add',
                'https://app.hubx.com/listings/new'
            ],
            'selectors': {
                'product_name': ['input[name="name"]', 'input[name="title"]'],
                'quantity': ['input[name="quantity"]'],
                'price': ['input[name="price"]'],
                'condition': ['select[name="condition"]'],
                'description': ['textarea[name="description"]']
            }
        },
        'success_indicators': ['dashboard', 'inventory', 'sell', 'logout'],
        'rate_limit': {
            'listings_per_hour': 25,
            'delay_between_listings': 4
        }
    },
    
    'kadorf': {
        'name': 'Kadorf',
        'base_url': 'https://kadorf.com',
        'login': {
            'url': 'https://kadorf.com/login',
            'selectors': {
                'username': 'input#email',
                'password': 'input#password',
                'submit': 'input.y-button[type="submit"]',
                'cookie_accept': 'button.js-cookie-consent-agree.cookie-consent__agree'
            }
        },
        'has_2fa': None,  # To be tested
        '2fa_method': None,
        'listing': {
            'urls': [
                'https://kadorf.com/sell'
            ],
            'selectors': {
                'product_name': ['input[name="title"]'],
                'quantity': ['input[name="stock"]'],
                'price': ['input[name="price"]'],
                'condition': ['select[name="condition"]'],
                'description': ['textarea[name="description"]']
            }
        },
        'success_indicators': ['panel', 'listings', 'account', 'logout'],
        'rate_limit': {
            'listings_per_hour': 20,
            'delay_between_listings': 5
        }
    },

    'handlot': {
        'name': 'Handlot',
        'base_url': 'https://www.handlot.com',
        'login': {
            'url': 'https://www.handlot.com/login',
            'selectors': {
                'username': 'input[name="username"]',
                'password': 'input[name="password"]',
                'submit': 'button[type="submit"]'
            }
        },
        'has_2fa': None,  # To be tested
        '2fa_method': None,
        'listing': {
            'urls': [
                'https://www.handlot.com/add-product',
                'https://www.handlot.com/sell'
            ],
            'selectors': {
                'product_name': ['input[name="name"]'],
                'quantity': ['input[name="quantity"]'],
                'price': ['input[name="price"]'],
                'condition': ['select[name="condition"]'],
                'description': ['textarea[name="description"]']
            }
        },
        'success_indicators': ['dashboard', 'inventory', 'account', 'logout'],
        'rate_limit': {
            'listings_per_hour': 15,
            'delay_between_listings': 6
        }
    }
}

# Email patterns for 2FA code extraction
EMAIL_PATTERNS = {
    'gsmexchange': {
        'from_addresses': ['noreply@gsmexchange.com', 'support@gsmexchange.com'],
        'subject_keywords': ['verification', 'code', 'GSM Exchange'],
        'code_patterns': [
            r'code:\s*(\d{6})',
            r'verification code is (\d{6})',
            r'(\d{6}) is your code'
        ]
    },
    'cellpex': {
        'from_addresses': ['noreply@cellpex.com', 'support@cellpex.com'],
        'subject_keywords': ['Cellpex', 'verification', 'authentication'],
        'code_patterns': [
            r'code:\s*(\d{4,6})',
            r'verification code is (\d{4,6})'
        ]
    }
}

# Platform-specific form field mappings
FIELD_MAPPINGS = {
    'common': {
        'product_type': ['type', 'category', 'product_type'],
        'brand': ['brand', 'manufacturer', 'make'],
        'model': ['model', 'model_name', 'product_model'],
        'memory': ['memory', 'storage', 'capacity', 'gb'],
        'color': ['color', 'colour'],
        'carrier': ['carrier', 'network', 'operator'],
        'region': ['region', 'market', 'country'],
        'imei': ['imei', 'serial'],
        'warranty': ['warranty', 'guarantee'],
        'accessories': ['accessories', 'included', 'box_contents']
    }
}


def get_platform_config(platform_name: str) -> dict:
    """Get configuration for a specific platform"""
    platform_name = platform_name.lower()
    
    if platform_name not in PLATFORM_CONFIGS:
        raise ValueError(f"Platform '{platform_name}' not configured")
    
    return PLATFORM_CONFIGS[platform_name]


def get_all_platforms() -> list:
    """Get list of all configured platforms"""
    return list(PLATFORM_CONFIGS.keys())


def get_2fa_platforms() -> list:
    """Get list of platforms that require 2FA"""
    return [
        name for name, config in PLATFORM_CONFIGS.items()
        if config.get('has_2fa') is True
    ]


def get_platform_rate_limit(platform_name: str) -> dict:
    """Get rate limiting configuration for a platform"""
    config = get_platform_config(platform_name)
    return config.get('rate_limit', {
        'listings_per_hour': 10,
        'delay_between_listings': 10
    })


if __name__ == "__main__":
    # Display platform configurations
    print("📋 Configured Platforms:\n")
    
    for platform in get_all_platforms():
        config = get_platform_config(platform)
        print(f"🔹 {config['name']}:")
        print(f"   - Login URL: {config['login']['url']}")
        print(f"   - Has 2FA: {config['has_2fa']}")
        print(f"   - 2FA Method: {config['2fa_method']}")
        print(f"   - Rate Limit: {config['rate_limit']['listings_per_hour']} listings/hour")
        print()
    
    print(f"\n📱 Platforms requiring 2FA: {get_2fa_platforms()}")