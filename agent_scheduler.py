"""
Agent Scheduler - Automated scraping and watchlist monitoring
"""

import json
import time
from datetime import datetime, timedelta
from typing import List, Dict
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from gem_scraper import scrape_bids, download_document
from ai_analyzer import analyze_bid_complete
from database import CIPDatabase
from config import SCHEDULER_CONFIG, NOTIFICATION_CONFIG, FIRM_PROFILE


class CIPAgent:
    """Consulting Intelligence Platform Agent"""
    
    def __init__(self):
        self.db = CIPDatabase()
        self.scheduler = BackgroundScheduler(timezone=SCHEDULER_CONFIG['timezone'])
        self.is_running = False
    
    def daily_intelligence_run(self):
        """
        Daily scheduled scraping and analysis
        """
        print(f"[{datetime.now()}] Starting Daily Intelligence Run...")
        
        # Scrape consulting bids (using default settings)
        bids = scrape_bids(
            keywords="",  # Broad search
            from_date="",
            to_date="",
            max_pages=10,
            consulting_only=True
        )
        
        print(f"Found {len(bids)} consulting bids")
        
        analyzed_bids = []
        high_fit_bids = []
        
        for bid in bids:
            # Save bid to database
            self.db.save_bid(bid)
            
            # Download document for Virtual User analysis
            print(f"Downloading document for bid {bid['Bid Number']}...")
            pdf_path = download_document(bid['Document Link'], bid_data=bid)
            
            # Run AI analysis with Virtual User
            analysis = analyze_bid_complete(bid, pdf_path=pdf_path)
            
            # Save analysis
            self.db.save_ai_analysis(analysis)
            
            print(f"Bid {bid['Bid Number']} Analysis: Score={analysis['cfs']['score']}, Verdict={analysis['cfs']['verdict']}")
            if analysis['cfs'].get('reasoning'):
                print(f"Reasoning: {analysis['cfs']['reasoning'][:100]}...")

            analyzed_bids.append({
                "bid": bid,
                "analysis": analysis
            })
            
            # Filter high-fit bids
            if analysis['cfs']['score'] >= NOTIFICATION_CONFIG['min_cfs_score']:
                high_fit_bids.append({
                    "bid": bid,
                    "analysis": analysis
                })
        
        # Generate and save digest
        self.generate_digest(high_fit_bids)
        
        print(f"Daily run complete. Analyzed {len(analyzed_bids)} bids, {len(high_fit_bids)} high-fit")
        return len(high_fit_bids)
    
    def monitor_watchlist(self):
        """
        Check watchlist bids for changes
        """
        watchlist = self.db.get_watchlist()
        
        if not watchlist:
            print("Watchlist is empty")
            return
        
        print(f"[{datetime.now()}] Monitoring {len(watchlist)} bids...")
        
        changes_detected = []
        
        for bid_number in watchlist:
            # Get stored bid
            stored_bid = self.db.get_bid(bid_number)
            if not stored_bid:
                continue
            
            # Re-scrape this specific bid (would need API endpoint for single bid)
            # For now, we'll check if it appears in recent scrapes
            # In production, you'd scrape the specific bid page
            
            # Placeholder: Detect changes by comparing with fresh scrape
            # This is simplified - real implementation would parse bid detail page
            pass
        
        if changes_detected:
            self.notify_changes(changes_detected)
    
    def generate_digest(self, high_fit_bids: List[Dict], filename=None):
        """
        Generate daily digest file
        """
        from datetime import datetime
        import os
        
        if filename is None:
            digest_dir = NOTIFICATION_CONFIG['digest_path']
            if not os.path.exists(digest_dir):
                os.makedirs(digest_dir)
            
            timestamp = datetime.now().strftime('%Y-%m-%d')
            filename = os.path.join(digest_dir, f"digest_{timestamp}.json")
        
        digest_data = {
            "generated_at": datetime.now().isoformat(),
            "firm_name": FIRM_PROFILE['name'],
            "total_opportunities": len(high_fit_bids),
            "opportunities": []
        }
        
        for item in high_fit_bids:
            bid = item['bid']
            analysis = item['analysis']
            
            digest_data['opportunities'].append({
                "bid_number": bid['Bid Number'],
                "category": bid.get('Category', 'Unknown'),
                "items": bid['Items'],
                "department": bid['Department'],
                "end_date": bid['End Date'],
                "cfs_score": analysis['cfs']['score'],
                "cfs_verdict": analysis['cfs']['verdict'],
                "reasoning": analysis['cfs']['reasoning'],
                "recommendation": analysis['go_no_go']['overall_recommendation'],
                "executive_summary": analysis['executive_summary'],
                "document_link": bid['Document Link']
            })
        
        # Save as JSON
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(digest_data, f, indent=2, ensure_ascii=False)
        
        print(f"Digest saved to: {filename}")
        return filename
    
    def notify_changes(self, changes: List[Dict]):
        """
        Notify about watchlist changes
        """
        # For file-based notification
        digest_dir = NOTIFICATION_CONFIG['digest_path']
        if not os.path.exists(digest_dir):
            os.makedirs(digest_dir)
        
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M')
        filename = os.path.join(digest_dir, f"changes_{timestamp}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump({
                "detected_at": datetime.now().isoformat(),
                "changes": changes
            }, f, indent=2)
        
        print(f"Change notification saved to: {filename}")
    
    def start_scheduler(self):
        """
        Start the background scheduler
        """
        if self.is_running:
            print("Scheduler is already running")
            return
        
        # Daily intelligence run
        hour, minute = SCHEDULER_CONFIG['daily_run_time'].split(':')
        self.scheduler.add_job(
            self.daily_intelligence_run,
            trigger=CronTrigger(hour=int(hour), minute=int(minute)),
            id='daily_intelligence',
            name='Daily Intelligence Run',
            replace_existing=True
        )
        
        # Watchlist monitoring
        self.scheduler.add_job(
            self.monitor_watchlist,
            trigger=IntervalTrigger(hours=SCHEDULER_CONFIG['watchlist_interval_hours']),
            id='watchlist_monitor',
            name='Watchlist Monitor',
            replace_existing=True
        )
        
        self.scheduler.start()
        self.is_running = True
        
        print(f"Scheduler started. Daily run at {SCHEDULER_CONFIG['daily_run_time']}")
        print(f"Watchlist check every {SCHEDULER_CONFIG['watchlist_interval_hours']} hours")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            self.is_running = False
            print("Scheduler stopped")
    
    def run_now(self, job_name='daily_intelligence'):
        """
        Manually trigger a job
        """
        if job_name == 'daily_intelligence':
            return self.daily_intelligence_run()
        elif job_name == 'watchlist':
            return self.monitor_watchlist()


if __name__ == "__main__":
    # Test the agent
    agent = CIPAgent()
    
    # Run intelligence now
    print("Running intelligence gathering...")
    agent.run_now('daily_intelligence')
    
    # Or start scheduler
    # agent.start_scheduler()
    # 
    # # Keep running
    # try:
    #     while True:
    #         time.sleep(60)
    # except KeyboardInterrupt:
    #     agent.stop_scheduler()
