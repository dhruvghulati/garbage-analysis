# Testing Guide

## Quick Test with Sampling

To test the pipeline on a sample of 10 events without re-downloading existing data:

```bash
python3 main.py --url "https://www.youtube.com/watch?v=O3fAVQ8Wm60" --sample-size 10
```

This will:
1. ✅ Skip video download if already exists
2. ✅ Skip frame extraction if frames already exist
3. ✅ Skip clip extraction if clips already exist
4. ✅ Sample 10 random events that contain bins
5. ✅ Analyze only the sampled events with VLM (saves API costs)
6. ✅ Generate reports with sampling metadata

## View Results in Streamlit

After running the pipeline, launch the Streamlit dashboard:

```bash
streamlit run app.py
```

The dashboard will show:
- Total events detected
- Sampling information (if sampling was used)
- Filter options: "All Events", "Sampled Only", "Unsampled Only"
- Event badges: 🎲 SAMPLED or ⏭️ NOT ANALYZED
- Video clips for each event
- Timeline visualization

## Expected Outputs

After running the pipeline, check these locations:

- **Reports**: `outputs/reports/report_YYYYMMDD_HHMMSS.json` and `.md`
- **Clips**: `outputs/clips/{video_id}/event_XXX_tYYY.XXs.mp4`
- **Frames**: `outputs/frames/{video_id}/frame_XXXXXX_tYYY.XX.jpg`
- **Videos**: `outputs/videos/{video_id}.mp4`

## Verify Sampling in Reports

The JSON report will include sampling metadata:

```json
{
  "metadata": {
    "sampling_info": {
      "total_events": 81,
      "sampled_events": 10,
      "sample_size": 10,
      "sampling_method": "random_bin_events"
    }
  }
}
```

## Cost Control

The pipeline automatically limits VLM API costs to $1 per run (configurable via `MAX_VLM_COST_USD` in `config.py`). With `--sample-size 10`, you'll typically spend well under $0.50 for GPT-4o analysis.
