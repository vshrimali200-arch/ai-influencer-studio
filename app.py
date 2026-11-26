import streamlit as st
import sqlite3, os, json, csv, io, subprocess, shutil
from pathlib import Path
from datetime import date, datetime

BASE = Path(__file__).parent
DATA = BASE / 'data'
MEDIA = DATA / 'media'
DATA.mkdir(exist_ok=True)
MEDIA.mkdir(exist_ok=True)
DB = DATA / 'studio.db'

st.set_page_config(page_title='AI Influencer Studio', page_icon='✨', layout='wide')

@st.cache_resource
def db():
    con = sqlite3.connect(DB, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.executescript('''
    CREATE TABLE IF NOT EXISTS characters(id INTEGER PRIMARY KEY, name TEXT, handle TEXT, bio TEXT, visual_prompt TEXT, created_at TEXT);
    CREATE TABLE IF NOT EXISTS posts(id INTEGER PRIMARY KEY, character_id INTEGER, title TEXT, platform TEXT, post_type TEXT, caption TEXT, hashtags TEXT, status TEXT, scheduled_date TEXT, media_path TEXT, created_at TEXT);
    ''')
    return con
con = db()

st.markdown('''<style>
.block-container{padding-top:1.5rem;max-width:1250px}
[data-testid="stMetric"]{background:#171b28;padding:16px;border-radius:14px;border:1px solid #292f42}
.hero{padding:24px;border-radius:18px;background:linear-gradient(120deg,#202544,#321d45);border:1px solid #45405f;margin-bottom:18px}
.smallmuted{color:#a8afc2}
</style>''', unsafe_allow_html=True)

st.sidebar.title('✨ AI Influencer Studio')
page = st.sidebar.radio('Workspace', ['Overview','Characters','Content Studio','Reel Maker','Content Calendar','Settings'])
st.sidebar.caption('Free local MVP • Your files stay on this device')

characters = con.execute('SELECT * FROM characters ORDER BY id DESC').fetchall()

if page == 'Overview':
    st.markdown('<div class="hero"><h1>AI Influencer Studio</h1><p class="smallmuted">Create an original virtual creator, organize content, prepare Reels and track your publishing workflow.</p></div>', unsafe_allow_html=True)
    total_chars = con.execute('SELECT COUNT(*) FROM characters').fetchone()[0]
    total_posts = con.execute('SELECT COUNT(*) FROM posts').fetchone()[0]
    drafts = con.execute("SELECT COUNT(*) FROM posts WHERE status='Draft'").fetchone()[0]
    scheduled = con.execute("SELECT COUNT(*) FROM posts WHERE status='Scheduled'").fetchone()[0]
    a,b,c,d = st.columns(4)
    a.metric('Characters', total_chars); b.metric('Content items', total_posts); c.metric('Drafts', drafts); d.metric('Scheduled', scheduled)
    st.subheader('Quick start')
    st.markdown('1. Create an **original fictional character** in Characters.\n2. Add a photo/video or write a post in Content Studio.\n3. Assemble a simple image-based Reel in Reel Maker.\n4. Review and schedule content in Content Calendar.\n5. Publish manually through Instagram until official API access is configured.')
    st.info('This free version does not generate photorealistic AI images by itself or auto-publish to Instagram. It manages your character, assets, captions, drafts and calendar without paid API keys.')

elif page == 'Characters':
    st.title('👩 Character Manager')
    with st.form('character_form', clear_on_submit=True):
        name = st.text_input('Character name', placeholder='e.g. Nia Khanna')
        handle = st.text_input('Instagram-style handle', placeholder='e.g. nia.days')
        bio = st.text_area('Bio', placeholder='A fictional digital creator sharing art, music and everyday moments.')
        prompt = st.text_area('Character consistency prompt', placeholder='Describe original facial features, hairstyle, general style, and visual identity. Avoid copying a real person.')
        submitted = st.form_submit_button('Save character')
        if submitted:
            if not name.strip(): st.error('Please enter a character name.')
            else:
                con.execute('INSERT INTO characters(name,handle,bio,visual_prompt,created_at) VALUES(?,?,?,?,?)',(name.strip(),handle.strip(),bio.strip(),prompt.strip(),datetime.now().isoformat(timespec='seconds')))
                con.commit(); st.success('Character saved.'); st.rerun()
    st.divider()
    for ch in con.execute('SELECT * FROM characters ORDER BY id DESC').fetchall():
        with st.expander(f"{ch['name']}  •  @{ch['handle'] or 'no-handle'}"):
            st.write(ch['bio'] or 'No bio yet.')
            st.caption('Consistency prompt')
            st.write(ch['visual_prompt'] or 'No prompt saved.')
            if st.button('Delete character', key=f"delch{ch['id']}"):
                con.execute('DELETE FROM characters WHERE id=?',(ch['id'],)); con.execute('DELETE FROM posts WHERE character_id=?',(ch['id'],)); con.commit(); st.rerun()

elif page == 'Content Studio':
    st.title('✍️ Content Studio')
    if not characters: st.warning('Create a character first in Characters.'); st.stop()
    options = {f"{x['name']} (@{x['handle']})":x['id'] for x in characters}
    with st.form('post_form', clear_on_submit=True):
        chosen = st.selectbox('Character', list(options))
        title = st.text_input('Content title', placeholder='A little sunshine today')
        platform = st.selectbox('Platform', ['Instagram','YouTube Shorts','Other'])
        typ = st.selectbox('Format', ['Reel','Post','Story','Short'])
        theme = st.selectbox('Caption tone', ['Warm and relatable','Playful','Confident','Poetic','Minimal'])
        topic = st.text_input('What is this post about?', placeholder='Cafe visit, rainy day, music, travel...')
        caption = st.text_area('Caption', placeholder='Write or paste your caption here.')
        tags = st.text_input('Hashtags', placeholder='#aicreator #lifestyle #reels')
        status = st.selectbox('Status', ['Draft','Ready for review','Scheduled','Published'])
        scheduled = st.date_input('Planned date', value=date.today())
        upload = st.file_uploader('Attach image/video (optional)', type=['png','jpg','jpeg','webp','mp4','mov'])
        save = st.form_submit_button('Save content')
        if save:
            path = ''
            if upload:
                safe = ''.join(c for c in upload.name if c.isalnum() or c in '._-')
                path = str(MEDIA / f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{safe}")
                with open(path,'wb') as f: f.write(upload.getbuffer())
            con.execute('INSERT INTO posts(character_id,title,platform,post_type,caption,hashtags,status,scheduled_date,media_path,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)', (options[chosen],title,platform,typ,caption,tags,status,str(scheduled),path,datetime.now().isoformat(timespec='seconds')))
            con.commit(); st.success('Content saved.')
    st.subheader('Free caption starter')
    tone = st.selectbox('Choose a tone', ['Warm and relatable','Playful','Confident','Poetic','Minimal'], key='caption_tone')
    subject = st.text_input('Topic for caption starter', key='caption_topic')
    if st.button('Create caption idea'):
        starters = {
          'Warm and relatable': f"Little moments, lasting memories. {subject}" if subject else 'Little moments, lasting memories. ✨',
          'Playful': f"A little mood, a lot of memories. {subject} 😄" if subject else 'A little mood, a lot of memories. 😄',
          'Confident': f"Showing up as my own kind of different. {subject}" if subject else 'Showing up as my own kind of different. ✨',
          'Poetic': f"Some days feel like a song without words. {subject}" if subject else 'Some days feel like a song without words. 🌙',
          'Minimal': f"Just this moment. {subject}" if subject else 'Just this moment. ✨'}
        st.code(starters[tone])
    st.divider(); st.subheader('Saved content')
    rows = con.execute('SELECT posts.*,characters.name AS cname FROM posts LEFT JOIN characters ON posts.character_id=characters.id ORDER BY posts.id DESC').fetchall()
    for p in rows:
        with st.expander(f"{p['title'] or 'Untitled'} • {p['cname']} • {p['status']} • {p['scheduled_date']}"):
            st.write(p['caption']); st.caption(p['hashtags'])
            if p['media_path'] and Path(p['media_path']).exists():
                ext=Path(p['media_path']).suffix.lower()
                if ext in ['.png','.jpg','.jpeg','.webp']: st.image(p['media_path'], width=320)
                else: st.video(p['media_path'])
            if st.button('Delete content', key=f"delpost{p['id']}"):
                if p['media_path'] and Path(p['media_path']).exists(): Path(p['media_path']).unlink()
                con.execute('DELETE FROM posts WHERE id=?',(p['id'],)); con.commit(); st.rerun()

elif page == 'Reel Maker':
    st.title('🎬 Simple Reel Maker')
    st.write('Create a basic vertical slideshow video from your own images. Requires FFmpeg installed on your computer.')
    if shutil.which('ffmpeg') is None:
        st.warning('FFmpeg was not detected. Install FFmpeg and restart the app to enable video export. You can still prepare images and captions in Content Studio.')
    files = st.file_uploader('Upload 2–12 images in order', type=['jpg','jpeg','png','webp'], accept_multiple_files=True)
    duration = st.slider('Seconds per image', 1, 6, 3)
    if st.button('Build vertical Reel', disabled=(not files or len(files)<2 or len(files)>12 or shutil.which('ffmpeg') is None)):
        tmp=DATA/'reel_frames'; tmp.mkdir(exist_ok=True)
        for f in tmp.iterdir():
            if f.is_file(): f.unlink()
        for i,f in enumerate(files):
            ext=Path(f.name).suffix.lower() or '.jpg'; (tmp/f'frame_{i:02d}{ext}').write_bytes(f.getbuffer())
        # Normalize still images into a vertical 1080x1920 slideshow.
        inputs=[]
        for i,f in enumerate(files):
            src=tmp/f'frame_{i:02d}{Path(f.name).suffix.lower()}'
            out=tmp/f'norm_{i:02d}.mp4'
            cmd=['ffmpeg','-y','-loop','1','-i',str(src),'-t',str(duration),'-vf',"scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,format=yuv420p",'-r','30','-an',str(out)]
            subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
            inputs.append(out)
        listing=tmp/'list.txt'; listing.write_text(''.join(f"file '{x.as_posix()}'\n" for x in inputs))
        output=DATA/'ai_influencer_reel.mp4'
        result=subprocess.run(['ffmpeg','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy',str(output)],capture_output=True)
        if result.returncode==0:
            st.success('Reel created.'); st.video(str(output)); st.download_button('Download Reel', output.read_bytes(), file_name='ai_influencer_reel.mp4', mime='video/mp4')
        else: st.error('FFmpeg could not assemble this set of images. Try JPG or PNG images.')

elif page == 'Content Calendar':
    st.title('📅 Content Calendar')
    rows=con.execute('SELECT posts.*,characters.name AS cname FROM posts LEFT JOIN characters ON posts.character_id=characters.id ORDER BY scheduled_date ASC').fetchall()
    if not rows: st.info('No content planned yet. Add posts in Content Studio.'); st.stop()
    for p in rows:
        col1,col2,col3=st.columns([2,1,1])
        col1.write(f"**{p['scheduled_date']}** — {p['title'] or 'Untitled'} ({p['cname']})")
        col2.write(p['platform']+' / '+p['post_type'])
        col3.write(p['status'])
    st.divider()
    output=io.StringIO(); writer=csv.writer(output); writer.writerow(['Date','Character','Title','Platform','Format','Caption','Hashtags','Status'])
    for p in rows: writer.writerow([p['scheduled_date'],p['cname'],p['title'],p['platform'],p['post_type'],p['caption'],p['hashtags'],p['status']])
    st.download_button('Export calendar as CSV',output.getvalue(),file_name='content_calendar.csv',mime='text/csv')

else:
    st.title('⚙️ Settings & integrations')
    st.subheader('Free-first setup')
    st.markdown('- **Storage:** local SQLite database and `data/media` folder.\n- **Images/videos:** upload assets you create or have permission to use.\n- **Video editing:** optional local FFmpeg.\n- **AI generation:** connect a provider later; free tiers and limits change.\n- **Instagram publishing:** use Meta’s official Instagram API where your account and app are eligible; otherwise publish manually.')
    st.warning('Do not paste API secrets into shared screenshots or commit them to Git. This starter app does not request or store passwords.')
    st.subheader('Backup')
    st.download_button('Download database backup',DB.read_bytes(),file_name='studio_backup.db',mime='application/octet-stream')
    st.caption('To back up uploaded media too, copy the entire data folder.')

st.sidebar.divider()
st.sidebar.caption('AI-generated character should be clearly represented as fictional/AI where relevant. Review all content before publishing.')
