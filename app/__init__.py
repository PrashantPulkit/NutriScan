from datetime import datetime
from itertools import combinations, product
import json
import random
from flask import Flask, flash, jsonify, redirect, session, url_for
from flask import render_template,request
import nltk
from pyzbar.pyzbar import decode
import cv2
import re
#import pymongo
from PIL import Image
import os
import uuid
import numpy as np
import requests
from textblob import TextBlob
from nltk import word_tokenize, pos_tag, ne_chunk
from app.models import get_db_connection
from app.models import db , User

from .AdminRoutes import my_routes

'''
# MongoDB setup
client = pymongo.MongoClient("mongodb://localhost:27017/")  # Adjust URI as needed
db = client['nutriscan_db']
alt_collection = db['alternative_products'] 
'''

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')
    app.register_blueprint(my_routes)


    db.init_app(app)

    # Create all tables
    with app.app_context():
        db.create_all()

    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/submitnew')
    def submitnew():
        return render_template('submit_product.html')
   

    @app.route('/history')
    def history():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, barcode, status, searched_at FROM search_history ORDER BY searched_at DESC")
        history_data = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('history.html', history=history_data) 

    
    @app.route('/search', methods=['POST'])
    def search():
        barcode = None

        # Option 1: Manual entry
        if 'barcode' in request.form and request.form['barcode']:
            barcode = request.form['barcode']

        # Option 2: Uploaded image
        elif 'image' in request.files:
            image_file = request.files['image']
            if image_file.filename != '':
                file_bytes = np.frombuffer(image_file.read(), np.uint8)
                img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

                decoded_objs = decode(img)
                if decoded_objs:
                    barcode = decoded_objs[0].data.decode('utf-8')

        # ✅ NEW LOGIC: If no barcode found, treat input as text search
        if not barcode:
            query = request.form.get('product_name')
            print("+++++++++++++++++++++++++++++",query)  # reuse same input field
            product=fetch_product_info(query)
            print("inside main product page dsplay name search after product")
            nutriments = product.get('nutriments', {})

            product_info = {
                'name': product.get('product_name', 'N/A'),
                'brands': product.get('brands', 'N/A'),
                'quantity': product.get('quantity', 'N/A'),
                'packaging': product.get('packaging', 'N/A'),
                'categories': product.get('categories', 'N/A'),
                'image_url': product.get('image_url', ''),
                'nutriscore': product.get('nutriscore_grade', 'N/A'),
                'ecoscore': product.get('ecoscore_grade', 'N/A'),
                'nova_group': product.get('nova_group', 'N/A'),
                'ingredients_text': product.get('ingredients_text', 'N/A'),
                'allergens': product.get('allergens_tags', []),
                'additives': product.get('additives_tags', []),
                'nutriments': {
                    'energy_kcal': nutriments.get('energy-kcal_100g', 'N/A'),
                    'fat': nutriments.get('fat_100g', 'N/A'),
                    'saturated_fat': nutriments.get('saturated-fat_100g', 'N/A'),
                    'carbohydrates': nutriments.get('carbohydrates_100g', 'N/A'),
                    'sugars': nutriments.get('sugars_100g', 'N/A'),
                    'fiber': nutriments.get('fiber_100g', 'N/A'),
                    'proteins': nutriments.get('proteins_100g', 'N/A'),
                    'salt': nutriments.get('salt_100g', 'N/A'),
                    'sodium': nutriments.get('sodium_100g', 'N/A')
                },
                'barcode': product.get('code')

            }
            print("categories" + f"{product.get('categories_tags', [])}")
            barcode = product_info['barcode']
            if not product:
                return render_template('product_detail.html', not_found=True)

            # 👇 Render results list (you must create search_results.html)
            return render_template('product_detail.html', product= product_info)

        # If we have a barcode, fetch product data
        product_url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(product_url)
        data = response.json()

        # Store in DB
       

        

        product = data['product']
        nutriments = product.get('nutriments', {})

        product_info = {
            'name': product.get('product_name', 'N/A'),
            'brands': product.get('brands', 'N/A'),
            'quantity': product.get('quantity', 'N/A'),
            'packaging': product.get('packaging', 'N/A'),
            'categories': product.get('categories', 'N/A'),
            'image_url': product.get('image_url', ''),
            'nutriscore': product.get('nutriscore_grade', 'N/A'),
            'ecoscore': product.get('ecoscore_grade', 'N/A'),
            'nova_group': product.get('nova_group', 'N/A'),
            'ingredients_text': product.get('ingredients_text', 'N/A'),
            'allergens': product.get('allergens_tags', []),
            'additives': product.get('additives_tags', []),
            'nutriments': {
                'energy_kcal': nutriments.get('energy-kcal_100g', 'N/A'),
                'fat': nutriments.get('fat_100g', 'N/A'),
                'saturated_fat': nutriments.get('saturated-fat_100g', 'N/A'),
                'carbohydrates': nutriments.get('carbohydrates_100g', 'N/A'),
                'sugars': nutriments.get('sugars_100g', 'N/A'),
                'fiber': nutriments.get('fiber_100g', 'N/A'),
                'proteins': nutriments.get('proteins_100g', 'N/A'),
                'salt': nutriments.get('salt_100g', 'N/A'),
                'sodium': nutriments.get('sodium_100g', 'N/A')
            },
            'barcode': barcode
        }
        conn = get_db_connection()
        cursor = conn.cursor()
        status = 'found' if data.get('status') == 1 else 'not found'
        if product.get('nutriscore_grade', 'e') not in ['a','b','c','d','e']:
            score = "c"
        else:
            score= product.get('nutriscore_grade', 'e')    
        print(barcode,status,score)
        cursor.execute("INSERT INTO search_history (barcode, status,score) VALUES (%s, %s, %s)", (barcode, status,score))
        conn.commit()
        cursor.close()
        conn.close()
        print("categories" + f"{product.get('categories_tags', [])}")
        

        return render_template('product_detail.html', product=product_info)



    @app.route('/product/<barcode>')
    def product_detail(barcode):
        product_url = f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json"
        response = requests.get(product_url)
        data = response.json()

        if data.get('status') != 1:
            return "Product not found", 404

        product = data['product']
        nutriments = product.get('nutriments', {})

        product_info = {
            'name': product.get('product_name', 'N/A'),
            'brands': product.get('brands', 'N/A'),
            'quantity': product.get('quantity', 'N/A'),
            'packaging': product.get('packaging', 'N/A'),
            'categories': product.get('categories', 'N/A'),
            'image_url': product.get('image_url', ''),
            'nutriscore': product.get('nutriscore_grade', 'N/A'),
            'ecoscore': product.get('ecoscore_grade', 'N/A'),
            'nova_group': product.get('nova_group', 'N/A'),
            'ingredients_text': product.get('ingredients_text', 'N/A'),
            'allergens': product.get('allergens_tags', []),
            'additives': product.get('additives_tags', []),
            'nutriments': {
                'energy_kcal': nutriments.get('energy-kcal_100g', 'N/A'),
                'fat': nutriments.get('fat_100g', 'N/A'),
                'saturated_fat': nutriments.get('saturated-fat_100g', 'N/A'),
                'carbohydrates': nutriments.get('carbohydrates_100g', 'N/A'),
                'sugars': nutriments.get('sugars_100g', 'N/A'),
                'fiber': nutriments.get('fiber_100g', 'N/A'),
                'proteins': nutriments.get('proteins_100g', 'N/A'),
                'salt': nutriments.get('salt_100g', 'N/A'),
                'sodium': nutriments.get('sodium_100g', 'N/A')
            },
            'barcode': barcode
        }
        print("categories" +f"{ product.get('categories_tags', [])}")

        return render_template("product_detail.html", product=product_info)


    @app.route('/alternative')
    def alternative_products():
        barcode = request.args.get('barcode')
        if not barcode:
            return "No barcode provided", 400

        # Step 1: Get product info from barcode
        response = requests.get(f"https://world.openfoodfacts.org/api/v0/product/{barcode}.json")
        data = response.json()

        if data.get('status') != 1:
            return "Product not found", 404

        product = data['product']
        nutriscore = product.get('nutriscore_grade', 'e')
        categories = product.get('categories_tags', [])
        print("categ ---- "+f"{categories}")
        
        
        if "en:candies" in categories:
            category= "en:candies"
        elif "en:sodas" in categories:
            category= "sodas"
        elif "en:butters" in categories:
            category= "en:butters"
        elif "en:textured-soy-protein" in categories:
            category= "en:textured-soy-protein"
        elif "en:tomato-sauces" in categories:
            category= "en:tomato-sauces"
        elif "en:tomato-ketchup" in categories:
            category= "en:tomato-ketchup"
        elif "en:canned-fishes" in categories:
            category= "en:canned-fishes"
        elif "en:corn-chips" in categories:
            category= "en:corn-chips"
        elif "en:chips-and-fries" in categories:
            category= "en:chips-and-fries"
        else:
            category = categories[0] if categories else None

        if not category:
            return "No category found for product", 404
        

        cache_file = 'alterrnatives_cache.json'
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cache = json.load(f)
        else:
            cache = {}

        if category in cache:
            alternatives = cache[category]
            print('used cache ____________________________________________________')
            return render_template("alternative.html", alternatives=alternatives, original=product.get('product_name', 'Unknown'))

        # Step 2: Find better nutriscores
        grades_order = ['a', 'b', 'c', 'd', 'e']
        try:
            index = grades_order.index(nutriscore)
            better_grades = grades_order[1:index]  # grades better than current
        except ValueError:
            better_grades = ['a', 'b']  # default fallback

        # Step 3: Search with pagination
        search_url = "https://world.openfoodfacts.org/api/v2/search"
        page = 1
        max_results = 20
        page_size = 20
        alternatives = []

        while len(alternatives) < max_results:
            params = {
                "categories_tags": category,
                "nutrition_grades_tags": "|".join(better_grades),
                "fields": "product_name,brands,code,nutrition_grades_tags",
                "sort_by": "nutriscore_score",
                "page_size": page_size,
                "page": page
            }

            alt_response = requests.get(search_url, params=params)
            print(alt_response.text)
            alt_data = alt_response.json()
         
            products = alt_data.get('products', [])

            if not products:
                break  # no more results

            for item in products:
                if len(alternatives) >= max_results:
                    break
                if item.get('product_name') and item.get('code'):
                    alternatives.append({
                        'name': item.get('product_name', 'Unnamed'),
                        'brand': item.get('brands', 'Unknown'),
                        'barcode': item.get('code'),
                        'nutriscore': item.get('nutrition_grades_tags', ['?'])[0]
                    })

            page += 1
        cache[category] = alternatives
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)
        return render_template("alternative.html", alternatives=alternatives, original=product.get('product_name', 'Unknown'))

    #********************************************************************************************************************************
    #**********************************************chatbot logic************************************************************
    
    # Regex pattern for fallback
    nltk.download('punkt')
    nltk.download('averaged_perceptron_tagger')
    nltk.download('maxent_ne_chunker')

    nltk.download('maxent_ne_chunker_tab')
    nltk.download('words')

    # Regex pattern for fallback
    fallback_patterns = [
        r"(?:in|about|of|is|on|for|regarding)\s+([a-zA-Z0-9\s&'-]+)",  # Generic phrase pattern
        r"how much (?:calories|fat|protein|sugar|carbs)?\s*(?:is|are)?\s*(?:there)?\s*(?:in)?\s*([a-zA-Z0-9\s&'-]+)",  # Nutrient query
        r"tell me about\s+([a-zA-Z0-9\s&'-]+)",  # Tell me about pattern
        r"what can you tell me about\s+([a-zA-Z0-9\s&'-]+)",  # What can you tell about
        r"([a-zA-Z][a-zA-Z0-9\s&'-]+)"  # Fallback: catch anything that looks like a product
    ]

    # Function for NER-based extraction using NLTK
    def extract_product_name_ner_nltk(text):
        tokens = word_tokenize(text)
        tagged = pos_tag(tokens)  # Part of Speech tagging
        tree = ne_chunk(tagged)  # Named Entity Recognition
        
        # Extract named entities
        for subtree in tree:
            if isinstance(subtree, nltk.Tree):
                entity = " ".join(word for word, tag in subtree)
                if "NNP" in [tag for word, tag in subtree]:  # Proper Nouns (likely product names)
                    return entity
        return None

    # Function for noun-based extraction (first or longest noun)
    def extract_product_name_noun(text):
        tokens = word_tokenize(text)
        tagged = pos_tag(tokens)
        nouns = [word for word, tag in tagged if tag in ['NN', 'NNS', 'NNPS', 'NNP']]  # Noun tags
        
        if not nouns:
            return None

        # You can return the first noun or the longest noun
        longest_noun = max(nouns, key=len)
        return longest_noun

    # Fallback function using regex patterns
    def extract_product_name_regex(text):
        text = text.strip()
        for pattern in fallback_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()  # Return the matched product name
        return None

    # Combine all methods in one function
    def extract_product_name(text):
        # Step 1: Try NER first using NLTK
        product_name = extract_product_name_ner_nltk(text)
        if product_name:
            return product_name
        
        # Step 2: If NER doesn't find anything, try noun-based extraction
        product_name = extract_product_name_noun(text)
        if product_name:
            return product_name
        
        # Step 3: If neither works, fall back to regex extraction
        product_name = extract_product_name_regex(text)
        
        return product_name

    # Test cases
    test_sentences = [
        "How much protein is in a KitKat bar?",
        "Tell me about the Oats you have.",
        "What can you tell me about protein in cereal?",
        "Is the sugar content in KitKat high?",
        "I want to know more about almonds.",
        "Give me details about the new Coca-Cola product.",
        "Show me the list of cookies and snacks.",
        "What about the nutritional values of dairy products?",
        "Is this product safe for kids?",
        "Tell me about the benefits of almonds."
    ]

    for sentence in test_sentences:
        print(f"Input: {sentence}\nExtracted Product: {extract_product_name(sentence)}\n")


    # ✅ Fetch product info from Open Food Facts
    def fetch_product_info(product_name):
        product_name = product_name.lower()
        cache_file = 'product_cache.json'
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                cache = json.load(f)
        else:
            cache = {}

        if product_name in cache:
            print("Used cache______________________________________")
            return cache[product_name]

        url = f"https://world.openfoodfacts.org/cgi/search.pl?search_terms={product_name}&search_simple=1&action=process&json=1"
        response = requests.get(url)
        data = response.json()
        if data['products']:
            cache[product_name] = data['products'][0]
            with open(cache_file, 'w') as f:
                json.dump(cache, f, indent=2)
            return data['products'][0]
        else:
            return None

    # ✅ Analyze if product is healthy
    def analyze_health(product_data):
        nutri_score = product_data.get('nutriscore_grade', '')
        if nutri_score in ['a', 'b']:
            return "✅ This product is considered healthy based on its nutrition score!"
        elif nutri_score in ['c', 'd', 'e']:
            return "⚠️ This product is not very healthy. Consider a better alternative."
        else:
            return "❓ I couldn't find enough nutrition info for a health analysis."

    # ✅ Analyze if product is suitable for diabetes
    def analyze_diabetes(product_data):
        nutriments = product_data.get('nutriments', {})
        sugars = nutriments.get('sugars_100g')
        gi = nutriments.get('glycemic_index_100g') or nutriments.get('glycemic_index')

        sugar_info = ""
        if sugars is not None:
            if sugars <= 5:
                sugar_info = "✅ Low sugar (≤5g/100g)"
            elif sugars <= 10:
                sugar_info = "⚠️ Moderate sugar (5–10g/100g)"
            else:
                sugar_info = "❌ High sugar (>10g/100g)"
        else:
            sugar_info = "❓ Sugar content not found"

        gi_info = ""
        if gi is not None:
            gi = float(gi)
            if gi < 55:
                gi_info = "✅ Low GI (<55), suitable for diabetics"
            elif gi <= 70:
                gi_info = "⚠️ Moderate GI (55–70), caution advised"
            else:
                gi_info = "❌ High GI (>70), not suitable for diabetics"
        else:
            gi_info = "❓ Glycemic Index not available"

        return f"{sugar_info}\n{gi_info}"

    # ✅ Get nutrient info
    def get_nutrient_info(product_data, nutrient):
        nutriments = product_data.get('nutriments', {})
        value = nutriments.get(nutrient)
        unit = nutriments.get(f"{nutrient}_unit", "g")

        if value is not None:
            return f"The product contains {value} {unit} of {nutrient} per 100g."
        else:
            return f"Sorry, I couldn't find the {nutrient} content for this product."

    # ✅ Check if product is suitable for high blood pressure (low sodium)
    def analyze_high_bp(product_data):
        nutriments = product_data.get('nutriments', {})
        sodium = nutriments.get('sodium_100g')

        if sodium is not None:
            if sodium <= 0.1:
                return "✅ This product is low in sodium, which is good for high blood pressure."
            elif sodium <= 0.5:
                return "⚠️ This product has moderate sodium content. Consume in moderation if you have high blood pressure."
            else:
                return "❌ This product has high sodium, which is not suitable for people with high blood pressure."
        else:
            return "❓ Sodium content not found."

    # ✅ Check if product is suitable for low blood pressure (high sodium)
    def analyze_low_bp(product_data):
        nutriments = product_data.get('nutriments', {})
        sodium = nutriments.get('sodium_100g')

        if sodium is not None:
            if sodium >= 1.5:
                return "✅ This product has a high sodium content, which may help those with low blood pressure."
            elif sodium >= 1:
                return "⚠️ This product has moderate sodium. You may consume it if you need to raise blood pressure."
            else:
                return "❌ This product has low sodium, which may not be helpful for those with low blood pressure."
        else:
            return "❓ Sodium content not found."

    # ✅ Check if product is keto-friendly (high fat, low carbs)
    def analyze_keto_friendly(product_data):
        nutriments = product_data.get('nutriments', {})
        carbs = nutriments.get('carbohydrates_100g')
        fats = nutriments.get('fat_100g')

        if carbs is not None and fats is not None:
            if carbs < 5 and fats > 15:
                return "✅ This product is keto-friendly (high in fats, low in carbs)."
            elif carbs < 10 and fats > 10:
                return "⚠️ This product is somewhat keto-friendly but not ideal."
            else:
                return "❌ This product is not keto-friendly (high in carbs, low in fats)."
        else:
            return "❓ Carbs or fats information not found."

    # ✅ Get allergens info
    def get_allergens_info(product_data):
        allergens = product_data.get('allergens', [])
        if allergens:
            return f"⚠️ This product contains allergens: {', '.join(allergens)}."
        else:
            return "✅ This product does not contain any allergens."

    # ✅ Improved: Decide type of query
    def determine_query_type(user_message):
        user_message = user_message.lower()

        # broader keyword matching
        if any(word in user_message for word in ["calorie", "energy", "kcal"]):
            return "calories"
        if any(word in user_message for word in ["carb", "carbohydrate"]):
            return "carbohydrates"
        if "protein" in user_message:
            return "proteins"
        if "fat" in user_message:
            return "fat"
        if any(word in user_message for word in ["healthy", "health", "nutritious", "good for health"]):
            return "health"
        if any(word in user_message for word in ["diabetes", "diabetic", "sugar", "glycemic", "low sugar"]):
            return "diabetes"
        if any(word in user_message for word in ["high blood pressure", "low sodium", "sodium"]):
            return "high_bp"
        if any(word in user_message for word in ["low blood pressure", "high sodium"]):
            return "low_bp"
        if any(word in user_message for word in ["keto", "low carb", "high fat"]):
            return "keto"
        if "allergens" in user_message:
            return "allergens"

        return "unknown"

    # ✅ Main chatbot API (smarter fallback)
    @app.route('/chatbot', methods=['POST'])
    def chatbot():
        user_message = request.json.get('message')

        greetings = ["hi", "hello", "hey", "how are you", "greetings", "salutations"]
        for greeting in greetings:
            if greeting in user_message.lower():
                if "polaris" in user_message.lower():
                    return jsonify({"reply": "Hello! I'm Polaris, your friendly chatbot assistant! How can I help you today?"})
                else:
                    return jsonify({"reply": "Hi there! How can I assist you today?"})

        product_name = extract_product_name(user_message)
        query_type = determine_query_type(user_message)

        if not product_name:
            if query_type in ["health", "diabetes", "high_bp", "low_bp", "keto", "allergens"]:
                return jsonify({"reply": f"Please provide the product name for analysis."})

        product_info = fetch_product_info(product_name)

        if not product_info:
            return jsonify({"reply": f"Sorry, I couldn't find any info on '{product_name}'."})

        if query_type == "health":
            response = analyze_health(product_info)
        elif query_type == "diabetes":
            response = analyze_diabetes(product_info)
        elif query_type == "high_bp":
            response = analyze_high_bp(product_info)
        elif query_type == "low_bp":
            response = analyze_low_bp(product_info)
        elif query_type == "keto":
            response = analyze_keto_friendly(product_info)
        elif query_type == "allergens":
            response = get_allergens_info(product_info)
        elif query_type in ["calories", "fat", "proteins", "carbohydrates"]:
            response = get_nutrient_info(product_info, query_type)
        else:
            response = ("I can tell you if a product is healthy, diabetic-friendly, suitable for high blood pressure, "
                        "keto-friendly, or contains allergens.\n"
                        "Try asking something like 'Is Maggi good for diabetics?' or 'How many calories in Nutella?'.")

        return jsonify({"reply": f"Product: {product_name}\n\n{response}"})
    
    @app.route('/register', methods=['GET','POST'])
    def register():
        username = request.form.get('username')  # use .form not .json
        email = request.form.get('email')
        password = request.form.get('password')

        if not username or not email or not password:
            flash("Please provide username, email, and password", "error")
            return redirect(url_for('register'))  # go back to signup page

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash("User already exists", "error")
            return redirect(url_for('register'))

        new_user = User(username=username, email=email)
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("User registered successfully! Redirecting to login...", "success")
        return redirect(url_for('login'))  # after flashing, send to login page
    # Login Route
    @app.route('/login', methods=['GET','POST'])
    def login():
        if request.method == 'GET':
            return render_template('login.html')
        
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            return redirect(url_for('index'))
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    # Logout Route
    @app.route('/logout', methods=['POST'])
    def logout():
        session.pop('user_id', None)
        return jsonify({"message": "Logged out successfully!"}), 200

    @app.route('/analysis')
    def analysis():
        # Fetch last 10 scanned barcodes and their timestamps
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT barcode, searched_at
            FROM search_history
            ORDER BY searched_at DESC
            LIMIT 7
        """)
        history_data = cursor.fetchall()
        cursor.close()
        conn.close()

        barcodes = [item[0] for item in history_data]
        timestamps = [item[1] for item in history_data]

        nutri_scores = []
        for barcode in barcodes:
            response = requests.get(f'https://world.openfoodfacts.net/api/v2/product/{barcode}?fields=product_name,nutrition_grades')
            data = response.json()
            nutri_score = data['product'].get('nutrition_grades', 'unavailable')
            nutri_scores.append(nutri_score)

        # Map Nutri-Score grades to numerical values
        score_map = {'a': 5, 'b': 4, 'c': 3, 'd': 2, 'e': 1, 'unavailable': 0}
        numeric_scores = [score_map.get(score, 0) for score in nutri_scores]

        # Calculate average score
        average_score = sum(numeric_scores) / len(numeric_scores) if numeric_scores else 0

        # Determine trend
        trend = "positive" if average_score >= 4 else "negative"

        # Prepare data for graph
        graph_data = {
            'timestamps': [datetime.strptime(ts, '%Y-%m-%d %H:%M:%S') for ts in timestamps],
            'scores': numeric_scores
        }

        return render_template('analysis.html', average_score=average_score, trend=trend, graph_data=graph_data)
    

    @app.route('/report')
    def report():
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query the last 10 product scores from the history table
        cursor.execute("SELECT score FROM search_history ORDER BY searched_at DESC LIMIT 10")
        scores = cursor.fetchall()

        grading_criteria = {'a': 5, 'b': 4, 'c': 3, 'd': 2, 'e': 1}
        score_values = []
        labels = []

        for (score,) in scores:
            score_lower = score.lower() if score else None
            numeric_score = grading_criteria.get(score_lower, 0)
            score_values.append(numeric_score)
            labels.append(score_upper if (score_upper := score.upper()) else "Unavailable")

        # Core Calculations
        average_score = sum(score_values) / len(score_values) if score_values else 0
        best_score = max(score_values, default=0)
        worst_score = min(score_values, default=0)
        total_products = len(score_values)
        good_choices = sum(1 for val in score_values if val >= 4)
        poor_choices = sum(1 for val in score_values if val <= 2)

        # Generate feedback based on average score
        if average_score >= 4.5:
            feedback = "🌟 Excellent! Your product choices are top-tier and very healthy."
        elif average_score >= 3.5:
            feedback = "✅ Good! You mostly pick healthy products, with some room for improvement."
        elif average_score >= 2.5:
            feedback = "⚖️ Average. Your selections are okay but could be healthier."
        elif average_score >= 1.5:
            feedback = "⚠️ Below Average. Many products could be improved nutrition-wise."
        else:
            feedback = "❌ Poor. Serious improvement needed in your product choices."

        cursor.close()
        conn.close()

        return render_template('report.html.jinja2',
                            labels=labels,
                            score_values=score_values,
                            average_score=round(average_score, 2),
                            best_score=best_score,
                            worst_score=worst_score,
                            total_products=total_products,
                            good_choices=good_choices,
                            poor_choices=poor_choices,
                            feedback=feedback)
    
    UPLOAD_FOLDER = 'uploads'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # JSON file to store products
    PRODUCTS_FILE = 'products.json'

    # Load existing products if file exists
    if os.path.exists(PRODUCTS_FILE):
        with open(PRODUCTS_FILE, 'r') as f:
            product_db = json.load(f)
    else:
        product_db = {}

    # Allowed extensions
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

    def is_allowed(filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

    def save_products():
        with open(PRODUCTS_FILE, 'w') as f:
            json.dump(product_db, f, indent=4)

    @app.route('/submit_product', methods=['POST'])
    def submit_product():
        barcode_photo = request.files.get('barcode_photo')
        ingredient_photo = request.files.get('ingredient_photo')

        product_name = request.form.get('product_name')
        brand_name = request.form.get('brand_name')
        category = request.form.get('category')

        if not all([barcode_photo, ingredient_photo, product_name, brand_name, category]):
            return jsonify({'error': 'All fields are required'}), 400

        if not (is_allowed(barcode_photo.filename) and is_allowed(ingredient_photo.filename)):
            return jsonify({'error': 'Photos must be PNG, JPG, or JPEG'}), 400

        # Save photos
        barcode_filename = 'barcode_' + barcode_photo.filename
        ingredient_filename = 'ingredient_' + ingredient_photo.filename

        barcode_path = os.path.join(app.config['UPLOAD_FOLDER'], barcode_filename)
        ingredient_path = os.path.join(app.config['UPLOAD_FOLDER'], ingredient_filename)

        barcode_photo.save(barcode_path)
        ingredient_photo.save(ingredient_path)

        # Save product to memory
        product_db[product_name.lower()] = {
            'name': product_name,
            'brand': brand_name,
            'category': category,
            'barcode_photo': barcode_filename,
            'ingredient_photo': ingredient_filename
        }

        # Save to file
        save_products()

        return jsonify({'message': 'Product submitted successfully'})
    
    @app.route('/product/<product_name>', methods=['GET'])
    def show_product(product_name):
        product = product_db.get(product_name.lower())
        if not product:
            return f"<h2>Product '{product_name}' not found.</h2>", 404

        return render_template('product_details2.html', product=product)
    

    @app.route('/test')
    def test():
        print("Test route accessed")
        return "Test successful!"





    return app