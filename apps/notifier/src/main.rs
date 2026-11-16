//! FairMind notifier: a small app in the person's session that shows the FairMind agent's messages and,
//! on request, what the agent checks on this laptop and every message it has shown.
//!
//! Device management installs it with a config file holding FairMind's address and the organisation's
//! notifier secret. On first run it enrols with this laptop's serial number and keeps its own key in the
//! person's config folder. It reads nothing on the laptop beyond the serial number and the account name.

use serde::Deserialize;
use std::error::Error;
use std::fs;
use std::path::PathBuf;
use std::process::Command;
use std::sync::mpsc::{channel, RecvTimeoutError, Sender};
use std::sync::{Arc, Mutex};
use std::thread;
use std::time::Duration;
use tao::event::{Event, StartCause};
use tao::event_loop::{ControlFlow, EventLoopBuilder};
use tray_icon::menu::{Menu, MenuEvent, MenuItem, PredefinedMenuItem};
use tray_icon::{Icon, TrayIconBuilder};

type Res<T> = Result<T, Box<dyn Error + Send + Sync>>;

const POLL: Duration = Duration::from_secs(60);

#[derive(Deserialize, Clone)]
struct Config {
    url: String,
    secret: String,
}

#[derive(Deserialize, Clone)]
struct Message {
    id: String,
    text: String,
    at: String,
}

#[derive(Deserialize, Clone, Default)]
struct Inbox {
    organisation: Option<String>,
    messages: Vec<Message>,
    history: Vec<Message>,
    checks: Vec<String>,
    never: Vec<String>,
}

fn config_path() -> PathBuf {
    if let Ok(p) = std::env::var("FAIRMIND_NOTIFIER_CONFIG") {
        return PathBuf::from(p);
    }
    if cfg!(target_os = "macos") {
        PathBuf::from("/Library/Application Support/FairMind/notifier.json")
    } else {
        PathBuf::from(r"C:\ProgramData\FairMind\notifier.json")
    }
}

fn key_path() -> PathBuf {
    dirs::config_dir().unwrap_or_else(std::env::temp_dir).join("FairMind").join("notifier.key")
}

fn run(cmd: &str, args: &[&str]) -> String {
    Command::new(cmd).args(args).output().map(|o| String::from_utf8_lossy(&o.stdout).into_owned()).unwrap_or_default()
}

/// The laptop's serial number, the key FairMind uses to match this notifier with the agent on the same laptop.
fn serial() -> String {
    if cfg!(target_os = "macos") {
        let out = run("/usr/sbin/ioreg", &["-rd1", "-c", "IOPlatformExpertDevice"]);
        out.lines()
            .find(|l| l.contains("IOPlatformSerialNumber"))
            .and_then(|l| l.split('"').nth(3))
            .unwrap_or_default()
            .to_string()
    } else {
        run("powershell", &["-NoProfile", "-Command", "(Get-CimInstance Win32_BIOS).SerialNumber"]).trim().to_string()
    }
}

fn account() -> String {
    std::env::var("USER").or_else(|_| std::env::var("USERNAME")).unwrap_or_default()
}

fn enroll(cfg: &Config) -> Res<String> {
    #[derive(Deserialize)]
    struct Enrolled {
        key: String,
    }
    let body = serde_json::json!({ "secret": cfg.secret, "serial": serial(), "user": account() });
    let got: Enrolled = ureq::post(&format!("{}/enroll", cfg.url)).timeout(Duration::from_secs(20)).send_json(body)?.into_json()?;
    let path = key_path();
    if let Some(dir) = path.parent() {
        fs::create_dir_all(dir)?;
    }
    fs::write(&path, &got.key)?;
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&path, fs::Permissions::from_mode(0o600))?;
    }
    Ok(got.key)
}

fn key(cfg: &Config) -> Res<String> {
    match fs::read_to_string(key_path()) {
        Ok(k) if !k.trim().is_empty() => Ok(k.trim().to_string()),
        _ => enroll(cfg),
    }
}

/// Fetch messages; a key FairMind no longer knows means enrol again once.
fn fetch(cfg: &Config) -> Res<(String, Inbox)> {
    let k = key(cfg)?;
    let get = |k: &str| ureq::get(&format!("{}/messages", cfg.url)).set("Authorization", &format!("Bearer {k}")).timeout(Duration::from_secs(20)).call();
    match get(&k) {
        Ok(r) => Ok((k, r.into_json()?)),
        Err(ureq::Error::Status(401, _)) => {
            let fresh = enroll(cfg)?;
            Ok((fresh.clone(), get(&fresh)?.into_json()?))
        }
        Err(e) => Err(e.into()),
    }
}

fn ack(cfg: &Config, k: &str, ids: Vec<String>) -> Res<()> {
    ureq::post(&format!("{}/ack", cfg.url))
        .set("Authorization", &format!("Bearer {k}"))
        .timeout(Duration::from_secs(20))
        .send_json(serde_json::json!({ "ids": ids }))?;
    Ok(())
}

fn title(inbox: &Inbox) -> String {
    match &inbox.organisation {
        Some(o) if !o.is_empty() => format!("FairMind for {o}"),
        _ => "FairMind".to_string(),
    }
}

/// Show new messages, then tell FairMind they were shown so they never repeat.
fn poll(cfg: &Config, latest: &Arc<Mutex<Inbox>>) -> Res<()> {
    let (k, inbox) = fetch(cfg)?;
    let mut shown = Vec::new();
    for m in &inbox.messages {
        if notify_rust::Notification::new().summary(&title(&inbox)).body(&m.text).show().is_ok() {
            shown.push(m.id.clone());
        }
    }
    if !shown.is_empty() {
        ack(cfg, &k, shown)?;
    }
    *latest.lock().unwrap() = inbox;
    Ok(())
}

fn escape(s: &str) -> String {
    s.replace('&', "&amp;").replace('<', "&lt;").replace('>', "&gt;").replace('"', "&quot;")
}

fn list(items: &[String]) -> String {
    items.iter().map(|i| format!("<li>{}</li>", escape(i))).collect()
}

/// The "FairMind on this laptop" page: what is checked, what never is, and every message shown here.
fn about_page(inbox: &Inbox) -> String {
    let history: Vec<String> = inbox.messages.iter().chain(inbox.history.iter()).map(|m| format!("{} · {}", m.at.get(..10).unwrap_or(&m.at), m.text)).collect();
    let shown = if history.is_empty() { "<li>No messages yet.</li>".to_string() } else { list(&history) };
    format!(
        "<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>FairMind on this laptop</title>\
         <style>body{{font-family:-apple-system,Segoe UI,sans-serif;max-width:720px;margin:40px auto;padding:0 20px;color:#15171a;line-height:1.5}}\
         h1{{font-size:22px}}h2{{font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:#5a5f68;margin-top:28px}}</style></head>\
         <body><h1>{}</h1><p>Installed by your organisation. It never blocks anything you do.</p>\
         <h2>What it checks</h2><ul>{}</ul><h2>What it never does</h2><ul>{}</ul><h2>Messages it showed you</h2><ul>{}</ul></body></html>",
        escape(&format!("{} on this laptop", title(inbox))),
        list(&inbox.checks),
        list(&inbox.never),
        shown
    )
}

fn open_about(latest: &Arc<Mutex<Inbox>>) {
    let html = about_page(&latest.lock().unwrap());
    let path = std::env::temp_dir().join("fairmind-on-this-laptop.html");
    if fs::write(&path, html).is_ok() {
        let _ = open::that(&path);
    }
}

/// An orange square, the FairMind mark, drawn here so the binary needs no image file.
fn icon() -> Icon {
    let n = 32u32;
    let rgba: Vec<u8> = (0..n * n).flat_map(|_| [0xff, 0x6b, 0x35, 0xff]).collect();
    Icon::from_rgba(rgba, n, n).expect("valid icon")
}

fn poller(cfg: Config, latest: Arc<Mutex<Inbox>>) -> Sender<()> {
    let (tx, rx) = channel::<()>();
    thread::spawn(move || loop {
        if let Err(e) = poll(&cfg, &latest) {
            eprintln!("FairMind notifier: {e}");
        }
        match rx.recv_timeout(POLL) {
            Ok(()) | Err(RecvTimeoutError::Timeout) => continue,
            Err(RecvTimeoutError::Disconnected) => break,
        }
    });
    tx
}

fn main() {
    let cfg: Config = match fs::read_to_string(config_path()).ok().and_then(|t| serde_json::from_str(&t).ok()) {
        Some(c) => c,
        None => {
            eprintln!("FairMind notifier: no settings at {}; your device management installs them.", config_path().display());
            std::process::exit(1);
        }
    };
    if std::env::args().any(|a| a == "--once") {
        // For device management checks and testing: one round, no menu bar icon.
        let latest = Arc::new(Mutex::new(Inbox::default()));
        match poll(&cfg, &latest) {
            Ok(()) => {
                let inbox = latest.lock().unwrap();
                println!("ok: {} new, {} shown before", inbox.messages.len(), inbox.history.len());
            }
            Err(e) => {
                eprintln!("FairMind notifier: {e}");
                std::process::exit(1);
            }
        }
        return;
    }

    let latest = Arc::new(Mutex::new(Inbox::default()));
    let check_now = poller(cfg, latest.clone());
    let event_loop = EventLoopBuilder::new().build();
    let about = MenuItem::new("What FairMind checks on this laptop", true, None);
    let check = MenuItem::new("Check for messages now", true, None);
    let quit = MenuItem::new("Quit", true, None);
    let menu = Menu::new();
    let _ = menu.append_items(&[&about, &check, &PredefinedMenuItem::separator(), &quit]);
    let mut tray = None;
    let menu_events = MenuEvent::receiver();

    event_loop.run(move |event, _, flow| {
        *flow = ControlFlow::WaitUntil(std::time::Instant::now() + Duration::from_millis(250));
        if let Event::NewEvents(StartCause::Init) = event {
            // macOS wants the menu bar icon created once the event loop runs.
            tray = TrayIconBuilder::new().with_menu(Box::new(menu.clone())).with_tooltip("FairMind").with_icon(icon()).build().ok();
        }
        if let Ok(e) = menu_events.try_recv() {
            if e.id == about.id() {
                open_about(&latest);
            } else if e.id == check.id() {
                let _ = check_now.send(());
            } else if e.id == quit.id() {
                tray.take();
                *flow = ControlFlow::Exit;
            }
        }
    });
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn about_page_escapes_and_lists() {
        let inbox = Inbox {
            organisation: Some("Acme <Ltd>".into()),
            messages: vec![Message { id: "1".into(), text: "Close <DeepSeek>".into(), at: "2026-11-17T10:00:00Z".into() }],
            history: vec![],
            checks: vec!["Which AI apps start".into()],
            never: vec!["Read your files".into()],
        };
        let page = about_page(&inbox);
        assert!(page.contains("FairMind for Acme &lt;Ltd&gt; on this laptop"));
        assert!(page.contains("2026-11-17 · Close &lt;DeepSeek&gt;"));
        assert!(page.contains("<li>Read your files</li>") && !page.contains("<DeepSeek>"));
    }

    #[test]
    fn title_without_organisation() {
        assert_eq!(title(&Inbox::default()), "FairMind");
    }
}
