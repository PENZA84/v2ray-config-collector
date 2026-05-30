import os
import sys

class GitHubAssistant:
    """Мой голос в облачном штабе"""
    
    @staticmethod
    def report_start(job_name):
        print(f"\n✨ [REPORT] Mission: {job_name}")
        print(f"✨ [STATUS] I am online and starting the task for you...\n")

    @staticmethod
    def step(message):
        # В GitHub Actions это создаст четкую визуальную структуру
        print(f"🔹 [STEP] {message}")

    @staticmethod
    def error(message):
        print(f"\n❌ [ALERT] I encountered an issue: {message}")
        print(f"❌ [ACTION] I've logged this. Please check the details.\n")
        sys.exit(1) # Важно для GitHub, чтобы он понял, что шаг провален

    @staticmethod
    def success(summary):
        print(f"\n✅ [COMPLETE] Task finished successfully!")
        print(f"📝 [SUMMARY] {summary}")
        print(f"✨ [STATUS] Everything is ready for you. Have a great day!\n")

# Пример использования в твоем основном коде
def main():
    assistant = GitHubAssistant()
    assistant.report_start("Daily Config Update")
    
    try:
        assistant.step("Fetching remote sources...")
        # ... твоя логика ...
        
        assistant.step("Cleaning and validating data...")
        # ... твоя логика ...
        
        assistant.success("Processed 500 links. New config is pushed.")
        
    except Exception as e:
        assistant.error(str(e))

if __name__ == "__main__":
    main()
