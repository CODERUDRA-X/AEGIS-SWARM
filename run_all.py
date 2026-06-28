import os
import json
import time
from dotenv import load_dotenv

# Imported all agents
from agents.scout import analyze_crowd_frame
from agents.risk import evaluate_risk
from agents.critic import challenge_risk_assessment
from agents.commander import generate_action_plan

load_dotenv()

def process_single_image(image_path, output_dir="outputs"):
    filename = os.path.basename(image_path)
    out_name = f"{os.path.splitext(filename)[0]}_report.json"
    out_path = os.path.join(output_dir, out_name)
    
    # to Skip if already processed (to saves API calls (✿◠‿◠)!!)
    if os.path.exists(out_path):
        print(f"⏩ Skipping {filename}, already processed.")
        return True

    print(f"\n🚀 Processing: {filename}...")
    try:
        #here i Run the swarm with small delays between calls to avoid bursting
        scout_out = analyze_crowd_frame(image_path)
        time.sleep(2) # 2 second breather 
        
        risk_out = evaluate_risk(scout_out)
        time.sleep(2)
        
        critic_out = challenge_risk_assessment(scout_out, risk_out)
        time.sleep(2)
        
        plan_out = generate_action_plan(critic_out)
        
        # Compile final report
        full_report = {
            "image": filename,
            "scout_data": json.loads(scout_out),
            "risk_assessment": json.loads(risk_out),
            "critic_review": json.loads(critic_out),
            "commander_plan": json.loads(plan_out)
        }
        
        # Save to JSON
        with open(out_path, "w") as f:
            json.dump(full_report, f, indent=2)
            
        print(f"✅ Saved report to: {out_path}")
        return True
        
    except Exception as e:
        print(f"❌ Failed on {filename}: {e}")
        return False

def process_all_images(input_dir="test_images", output_dir="outputs"):
    os.makedirs(output_dir, exist_ok=True)
    
    image_files = [f for f in os.listdir(input_dir) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))]
    
    for filename in image_files:
        image_path = os.path.join(input_dir, filename)
        success = process_single_image(image_path, output_dir)
        
        if not success:
            print("⏳ API Limit hit. Waiting 60 seconds before next image...")
            time.sleep(60) #by this Massive cooldown will be if an error happens

if __name__ == "__main__":
    process_all_images()