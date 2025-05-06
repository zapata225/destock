categories = [
    "Boissons",
    "Produits frais",
    "Épicerie",
    "Surgelés",
    "Produits laitiers",
    "Viandes et poissons"
]

products = [
    {
        "id": 1,
        "name": "Lot de 10 foie gras Labeyrie 285g",
        "description": "Foie gras de canard entier mi-cuit. Conditionnement : 12 boîtes/carton, 10 cartons/palette. DLC moyenne : 12-18 mois. Conservation : Au réfrigérateur entre 0°C et 4°C.",
        "price": 257.00,
        "category": "Produits frais",
        "stock": 15,
        "featured": False,
        "images": ["foie-gras.jpg", "foie-gras-2.jpg", "foie-gras-3.jpg"],
        "details": {
            "marque": "Labeyrie",
            "poids": "2.85kg (10x285g)",
            "conservation": "Au réfrigérateur",
            "origine": "France"
        }
    },
    {
        "id": 2,
        "name": "Saumon Fumé de Norvège 200g – Tranches Épaisses – Palette de 750 pièces",
        "description": "Saumon fumé de Norvège, tranches épaisses, 200g. Découvrez notre saumon fumé élevé en Norvège...",
        "price": 2550.00,
        "category": "Produits frais",
        "stock": 8,
        "featured": False,
        "images": ["saumon-fume.jpg", "saumon-fume-2.jpg", "saumon-fume-3.jpg"],
        "details": {
            "marque": "Norvège Premium",
            "poids": "200g/pièces",
            "conservation": "Au réfrigérateur",
            "origine": "Norvège"
        }
    },
    {
        "id": 3,
        "name": "Camembert AOP de Normandie au Lait Cru – Graindorge – 250g, avec 550 unités",
        "description": "Assortiment de 5 fromages français AOP, 1kg...",
        "price": 1760.00,
        "category": "Produits laitiers",
        "stock": 20,
        "featured": False,
        "images": ["fromages.jpg", "fromages-2.jpg", "fromages-3.jpg"],
        "details": {
            "marque": "Fromagerie Tradition",
            "poids": "137.5 kg",
            "conservation": "Au réfrigérateur",
            "origine": "France"
        }
    },
    {
        "id": 4,
        "name": "Champagne Brut Millésimé 75cl – Prestige – Lot de 125 bouteilles",
        "description": "Champagne brut millésimé, bouteille 75cl...",
        "price": 3375.00,
        "category": "Boissons",
        "stock": 25,
        "featured": False,
        "images": ["champagne.jpg", "champagne-2.jpg", "champagne-3.jpg"],
        "details": {
            "marque": "Maison de Champagne",
            "volume": "75cl",
            "alcool": "12%",
            "origine": "Champagne, France"
        }
    },
    {
        "id": 5,
        "name": "NATURELA - Café Grains Bio - Intenso - Arabica et Robusta- 400 paquets",
        "description": "NATURELA - Café Grains Bio - Intenso - Arabica et Robusta...",
        "price": 3560,
        "category": "Épicerie",
        "stock": 6,
        "featured": False,
        "images": ["cafe.jpg", "cafe-2.jpg", "cafe-3.jpg"],
        "details": {
            "marque": "Café Premium",
            "poids": "1kg",
            "torréfaction": "Moyenne",
            "origine": "Colombie"
        }
    },
    {
        "id": 6,
        "name": "🥩 Bavette d'Aloyau Wagyu Bio – 275g – 25 Pièces",
        "description": "Bavette d'Aloyau Wagyu Bio – 275g – Viande Persillée Exceptionnelle...",
        "price": 750.00,
        "category": "Viandes et poissons",
        "stock": 8,
        "featured": False,
        "images": ["wagyu.jpg", "wagyu-2.jpg", "wagyu-3.jpg"],
        "details": {
            "marque": "Wagyu Excellence",
            "poids": "275g",
            "conservation": "Surgelé",
            "origine": "Japon"
        }
    },
    {
        "id": 100,
        "name": "🥤 Palette de Coca-Cola Original – Bouteilles 1L",
        "description": "Lot de 144 bouteilles de Coca-Cola 1L - Destockage exceptionnel...",
        "price": 129.00,
        "category": "Boissons",
        "stock": 105,
        "featured": False,
        "images": ["palette-coca.jpg", "palette-coca1.jpg", "palette-coca2.jpg"],
        "details": {
            "marque": "Coca-Cola",
            "volume": "1L",
            "quantité": "144 bouteilles",
            "origine": "France"
        }
    },
    {
        "id": 101,
        "name": "🥤 Palette de RedBull (250ml)",
        "description": "Lot de 150 canettes de RedBull 250ml - Date limite longue...",
        "price": 2332.80,
        "category": "Boissons",
        "stock": 8,
        "featured": True,
        "images": ["palette-redbull.jpg", "palette-redbull1.jpg", "palette-redbull2.jpg"],
        "details": {
            "marque": "RedBull",
            "volume": "250ml",
            "quantité": "2592 canettes",
            "origine": "Autriche"
        }
    },
    {
        "id": 102,
        "name": "🥤 Fanta Orange 33cl",
        "description": "Boisson gazeuse rafraîchissante au goût d'orange naturelle...",
        "price": 1512.00,
        "category": "Boissons",
        "stock": 120,
        "featured": False,
        "images": ["fanta.jpg", "fanta-2.jpg", "fanta-3.jpg"],
        "details": {
            "marque": "Fanta",
            "volume": "33cl",
            "saveur": "Orange",
            "origine": "Pays-Bas"
        }
    },
    {
        "id": 103,
        "name": "⚡Palette Monster Energy 500ml (2 592 canettes)",
        "description": "Boisson énergisante Monster Energy pour un coup de boost instantané...",
        "price": 3456.00,
        "category": "Boissons",
        "stock": 95,
        "featured": True,
        "images": ["monster.jpg", "monster-2.jpg", "monster-3.jpg"],
        "details": {
            "marque": "Monster",
            "volume": "500ml",
            "type": "Énergisante",
            "origine": "USA"
        }
    },
    {
        "id": 104,
        "name": "Palette 🍊 Orangina 33cl",
        "description": "Boisson pétillante à base de jus d'orange avec pulpe...",
        "price": 928.80,
        "category": "Boissons",
        "stock": 110,
        "featured": False,
        "images": ["orangina.jpg", "orangina-2.jpg", "orangina-3.jpg"],
        "details": {
            "marque": "Orangina",
            "volume": "33cl",
            "saveur": "Orange",
            "origine": "France"
        }
    },
    {
        "id": 105,
        "name": "🍫 Nutella Pot 1kg en Palette, avec 432 pots de Nutella",
        "description": "Pâte à tartiner au cacao et aux noisettes...",
        "price": 1636.00,
        "category": "Épicerie",
        "stock": 80,
        "featured": True,
        "images": ["nutella.jpg", "nutella-2.jpg", "nutella-3.jpg"],
        "details": {
            "marque": "Nutella",
            "poids": "1kg",
            "composition": "Noisettes, cacao, lait écrémé",
            "origine": "Italie"
        }
    },
    {
        "id": 112,
        "name": "🍪 Palette de 1200 Paquets de Biscuits Nutella 304g",
        "description": "Palette contenant 1200 paquets de biscuits Nutella de 3040g...",
        "price": 3000.00,
        "category": "Épicerie",
        "stock": 5,
        "featured": False,
        "images": ["biscuits-nutella.jpg", "biscuits-nutella-2.jpg", "biscuits-nutella-3.jpg"],
        "details": {
            "marque": "Nutella",
            "quantité": "1200x304g",
            "origine": "France"
        }
    },
    {
        "id": 113,
        "name": "🥤 Palette de Canettes de Coca-Cola 33cl",
        "description": "Palette contenant des canettes de Coca-Cola au format 33cl...",
        "price": 1296.00,
        "category": "Boissons",
        "stock": 10,
        "featured": True,
        "images": ["coca.jpg", "coca-2.jpg", "coca-3.jpg"],
        "details": {
            "marque": "Coca-Cola",
            "volume": "33cl",
            "quantité": "2592 canettes",
            "origine": "France"
        }
    },
    {
        "id": 114,
        "name": "🧴 Palette Eau Gazeuse San Pellegrino – Bouteille 50 cl (600 unités)",
        "description": "Palette contenant 600 bouteilles d'eau gazeuse San Pellegrino de 50cl...",
        "price": 390.00,
        "category": "Boissons",
        "stock": 8,
        "featured": False,
        "images": ["san-pellegrino.jpg", "san-pellegrino-2.jpg", "san-pellegrino-3.jpg"],
        "details": {
            "marque": "San Pellegrino",
            "volume": "50cl",
            "quantité": "600 bouteilles",
            "origine": "Italie"
        }
    },
    {
        "id": 115,
        "name": "🍺 Palette de Canettes de Bière Heineken – 33 cl (2 592 canettes)",
        "description": "Palette contenant 2592 canettes de bière Heineken de 33cl...",
        "price": 1156.00,
        "category": "Boissons",
        "stock": 6,
        "featured": False,
        "images": ["heineken.jpg", "heineken-2.jpg", "heineken-3.jpg"],
        "details": {
            "marque": "Heineken",
            "volume": "33cl",
            "quantité": "2592 canettes",
            "origine": "Pays-Bas"
        }
    },
    {
        "id": 116,
        "name": "Palette de 960 bouteilles d'eau gazeuse Perrier fines bulles 50cl",
        "description": "Palette contenant 960 bouteilles d'eau gazeuse Perrier...",
        "price": 3990.00,
        "category": "Boissons",
        "stock": 7,
        "featured": False,
        "images": ["perrier-fines-bulles.jpg", "perrier-fines-bulles-2.jpg", "perrier-fines-bulles-3.jpg"],
        "details": {
            "marque": "Perrier",
            "volume": "50cl",
            "quantité": "960 bouteilles",
            "origine": "France"
        }
    },
    {
        "id": 117,
        "name": "💧 Palette de Bouteilles d'Eau Volvic Citron – 50 cl (1 152 bouteilles)",
        "description": "Palette contenant 1152 bouteilles d'eau Volvic citron de 50cl...",
        "price": 518.40,
        "category": "Boissons",
        "stock": 7,
        "featured": False,
        "images": ["volvic-citron.jpg", "volvic-citron-2.jpg", "volvic-citron-3.jpg"],
        "details": {
            "marque": "Volvic",
            "volume": "50cl",
            "quantité": "1152 bouteilles",
            "origine": "France"
        }
    },
    {
        "id": 118,
        "name": "🧃 Palette de Canettes de Lipton Ice Tea Pêche – 33 cl (2 592 canettes)",
        "description": "Palette contenant 2592 canettes de Lipton Ice Tea pêche de 33cl...",
        "price": 1263.60,
        "category": "Boissons",
        "stock": 7,
        "featured": False,
        "images": ["lipton-ice-tea.jpg", "lipton-ice-tea-2.jpg", "lipton-ice-tea-3.jpg"],
        "details": {
            "marque": "Lipton",
            "volume": "33cl",
            "saveur": "Pêche",
            "origine": "France"
        }
    },
    {
        "id": 119,
        "name": "☕ Palette de Capsules de Café Royal Espresso – 36 capsules par pack",
        "description": "Palette contenant 720 boîtes de capsules de café Café Royal Espresso...",
        "price": 5278.00,
        "category": "Épicerie",
        "stock": 5,
        "featured": True,
        "images": ["cafe-royal.jpg", "cafe-royal-2.jpg", "cafe-royal-3.jpg"],
        "details": {
            "marque": "Café Royal",
            "quantité": "720x36 capsules",
            "origine": "Suisse"
        }
    },
    {
        "id": 120,
        "name": "☕ Palette de 720 paquets de dosettes de café Senseo Classique (54 dosettes)",
        "description": "Palette contenant 720 paquets de dosettes de café Senseo Classique...",
        "price": 4500.00,
        "category": "Épicerie",
        "stock": 5,
        "featured": False,
        "images": ["senseo-classique.jpg", "senseo-classique-2.jpg", "senseo-classique-3.jpg"],
        "details": {
            "marque": "Senseo",
            "quantité": "720x54 dosettes",
            "origine": "France"
        }
    },
    {
        "id": 121,
        "name": "☕ Palette de 720 boîtes de capsules de café L'Or Espresso Delizioso (50 capsules)",
        "description": "Palette contenant 720 boîtes de capsules de café L'Or Espresso Delizioso...",
        "price": 5900.00,
        "category": "Épicerie",
        "stock": 5,
        "featured": False,
        "images": ["lor-espresso.jpg", "lor-espresso-2.jpg", "lor-espresso-3.jpg"],
        "details": {
            "marque": "L'Or",
            "quantité": "720x50 capsules",
            "origine": "France"
        }
    },
    {
        "id": 122,
        "name": "🍫 Lot de 100 boîtes Lindt Dubai Style 145g – USY",
        "description": "Palette contenant 960 tablettes de chocolat J.D. Gross Dubaï de 122g...",
        "price": 690.00,
        "category": "Épicerie",
        "stock": 5,
        "featured": False,
        "images": ["jd-gross-dubai.jpg", "jd-gross-dubai-2.jpg", "jd-gross-dubai-3.jpg"],
        "details": {
            "marque": "J.D. Gross",
            "poids": "122g",
            "quantité": "960 unités",
            "origine": "Allemagne"
        }
    },
    {
        "id": 200,
        "name": "🍾 Palette de Moët & Chandon Brut Impérial (240 bouteilles)",
        "description": "Palette contenant 240 bouteilles de Moët & Chandon Brut Impérial 75cl...",
        "price": 8100.00,
        "category": "Boissons",
        "stock": 2,
        "featured": True,
        "images": ["moet-chandon.jpg", "moet-chandon-1.jpg", "moet-chandon-2.jpg"],
        "details": {
            "marque": "Moët & Chandon",
            "volume": "75cl",
            "alcool": "12%",
            "origine": "Champagne, France"
        }
    },
    {
        "id": 201,
        "name": "🍾 Palette de Ruinart Blanc de Blancs (240 bouteilles)",
        "description": "Palette contenant 240 bouteilles de Ruinart Blanc de Blancs 75cl...",
        "price": 15300.00,
        "category": "Boissons",
        "stock": 1,
        "featured": True,
        "images": ["ruinart.jpg", "ruinart-1.jpg", "ruinart-3.jpg"],
        "details": {
            "marque": "Ruinart",
            "volume": "75cl",
            "alcool": "12.5%",
            "origine": "Champagne, France"
        }
    },
    {
        "id": 202,
        "name": "🍾 Palette de Dom Pérignon Vintage (480 bouteilles)",
        "description": "Palette contenant 480 bouteilles de Dom Pérignon Vintage 75cl...",
        "price": 25200.00,
        "category": "Boissons",
        "stock": 1,
        "featured": True,
        "images": ["dom-perignon.jpg", "dom-perignon-1.jpg", "dom-perignon-2.jpg"],
        "details": {
            "marque": "Dom Pérignon",
            "volume": "75cl",
            "alcool": "12.5%",
            "origine": "Champagne, France"
        }
    },
    {
        "id": 203,
        "name": "🍊 Palette de jus d'orange 1L (600 bouteilles)",
        "description": "Palette contenant 600 bouteilles de jus d'orange pur 1L...",
        "price": 562.00,
        "category": "Boissons",
        "stock": 6,
        "featured": False,
        "images": ["jus-orange.jpg", "jus-orange-2.jpg", "jus-orange-3.jpg"],
        "details": {
            "marque": "Jus Premium",
            "volume": "1L",
            "quantité": "600 bouteilles",
            "origine": "France"
        }
    },
    {
        "id": 204,
        "name": "Palette de jus de pomme 1L (600 bouteilles)",
        "description": "Palette contenant 600 bouteilles de jus de pomme pur 1L...",
        "price": 535.00,
        "category": "Boissons",
        "stock": 6,
        "featured": False,
        "images": ["jus-pomme.jpg", "jus-pomme-2.jpg", "jus-pomme-3.jpg"],
        "details": {
            "marque": "Jus Premium",
            "volume": "1L",
            "quantité": "600 bouteilles",
            "origine": "France"
        }
    },
    {
        "id": 205,
        "name": "Palette de jus d'ananas 1L (600 bouteilles)",
        "description": "Palette contenant 600 bouteilles de jus d'ananas pur 1L...",
        "price": 659.00,
        "category": "Boissons",
        "stock": 6,
        "featured": False,
        "images": ["jus-ananas.jpg"],
        "details": {
            "marque": "Jus Premium",
            "volume": "1L",
            "quantité": "600 bouteilles",
            "origine": "France"
        }
    },
    {
        "id": 206,
        "name": "Palette de biscuits Nutella 220g (1200 paquets)",
        "description": "Palette contenant 1200 paquets de biscuits Nutella 220g...",
        "price": 2996.00,
        "category": "Épicerie",
        "stock": 5,
        "featured": False,
        "images": ["biscuits-nutella.jpg"],
        "details": {
            "marque": "Nutella",
            "poids": "220g",
            "quantité": "1200 paquets",
            "origine": "France"
        }
    },
    {
        "id": 207,
        "name": "Palette de lait UHT 1L (1200 bouteilles)",
        "description": "Palette contenant 1200 bouteilles de lait UHT 1L...",
        "price": 800.00,
        "category": "Produits laitiers",
        "stock": 5,
        "featured": False,
        "images": ["lait-uht.jpg"],
        "details": {
            "marque": "Lactel",
            "volume": "1L",
            "quantité": "1200 bouteilles",
            "origine": "France"
        }
    },
    {
        "id": 208,
        "name": "🧃 Palette de Jus de Pomme Granini 25cl (960 bouteilles)",
        "description": "Palette contenant 960 bouteilles de jus de pomme Granini 25cl...",
        "price": 480.00,
        "category": "Boissons",
        "stock": 8,
        "featured": False,
        "images": ["jus-pomme-granini.jpg","jus-pomme-granini2.jpg","jus-pomme-granini3.jpg"],
        "details": {
            "marque": "Granini",
            "volume": "25cl",
            "quantité": "960 bouteilles",
            "origine": "Allemagne"
        }
    },
    {
        "id": 211,
        "name": "🍾 Palette de Champagne Laurent Perrier Brut 75cl (288 bouteilles)",
        "description": "Palette exclusive contenant 288 bouteilles de Champagne Laurent Perrier Brut 75cl. Idéal pour événements, réceptions ou revente. Élégance et prestige garantis.",
        "price": 3760.00,  # Prix promotionnel
        "old_price": 4896.00,  # Prix initial
        "category": "Boissons",
        "stock": 5,
        "featured": True,
        "images": ["laurent-perrier.jpg", "laurent-perrier-2.jpg", "laurent-perrier-3.jpg"],
        "details": {
            "marque": "Laurent Perrier",
            "volume": "75cl",
            "quantité": "288 bouteilles",
            "origine": "France",
            "type": "Champagne Brut",
            "conditionnement": "Palette"
        }
    }, 
    {
        "id": 209,
        "name": "💧 Palette d'Eau Minérale Evian 50cl (1152 bouteilles)",
        "description": "Palette contenant 1152 bouteilles d'eau minérale naturelle Evian 50cl...",
        "price": 576.00,
        "category": "Boissons",
        "stock": 10,
        "featured": False,
        "images": ["evian.jpg","evian-2.jpg"],
        "details": {
            "marque": "Evian",
            "volume": "50cl",
            "quantité": "1152 bouteilles",
            "origine": "France"
        }
    },
    {
        "id": 210,
        "name": "💧 Palette d'Eau de Source Cristaline 50cl (1152 bouteilles)",
        "description": "Palette contenant 1152 bouteilles d'eau de source Cristaline 50cl...",
        "price": 432.00,
        "category": "Boissons",
        "stock": 12,
        "featured": False,
        "images": ["cristaline.jpg","cristaline-2.jpg","cristaline-3.jpg"],
        "details": {
            "marque": "Cristaline",
            "volume": "50cl",
            "quantité": "1152 bouteilles",
            "origine": "France"
        }
    }
]
