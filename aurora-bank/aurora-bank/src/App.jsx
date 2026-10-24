
import "./App.css";
import Support from "./Support";

const services = [
  {
    icon: "↗",
    title: "Easy Transfers",
    description: "Move money with a simple, seamless digital banking experience.",
  },
  {
    icon: "▤",
    title: "Savings Accounts",
    description: "Build your future with savings options designed around you.",
  },
  {
    icon: "▣",
    title: "Cards & Payments",
    description: "Manage card payments and get help with transaction issues.",
  },
  {
    icon: "◷",
    title: "24/7 Assistance",
    description: "Get support for your banking queries whenever you need it.",
  },
];

function App() {
  if (window.location.pathname === "/support") {
  return <Support />;
}
  return (
    <div className="app">
      <div className="announcement">
        A brighter way to bank. Welcome to Aurora.
      </div>

      <header className="navbar">
        <a className="brand" href="#home">
          <span className="brand-mark">A</span>
          <span>
            <strong>AURORA</strong>
            <small>B A N K</small>
          </span>
        </a>

        <nav className="nav-links">
          <a href="#home">Home</a>
          <a href="#services">Our Services</a>
          <a href="#about">About Us</a>
        </nav>

        <a className="nav-button" href="/support">
          Get Support <span>↗</span>
        </a>
      </header>

      <main>
        <section className="hero" id="home">
          <div className="hero-content">
            <div className="eyebrow">
              <span className="status-dot" />
              BANKING, REIMAGINED
            </div>

            <h1>
              Your money.
              <br />
              Your future.
              <br />
              <span>Our commitment.</span>
            </h1>

            <p className="hero-description">
              Banking that moves with you. Experience a simpler,
              smarter way to manage your money, built around
              what matters most — you.
            </p>

            <div className="hero-actions">
              <a className="primary-button" href="#services">
                Explore Banking <span>↗</span>
              </a>
              <a className="secondary-button" href="/support">
                We're here to help
              </a>
            </div>

            <div className="trust-note">
              <span className="trust-icon">✓</span>
              Your goals. Your journey. Banking made personal.
            </div>
          </div>

          <div className="hero-visual">
            <div className="orbit orbit-one" />
            <div className="orbit orbit-two" />

            <div className="sun-glow" />

            <div className="bank-card">
              <div className="card-top">
                <span>AURORA</span>
                <span className="card-chip">◈</span>
              </div>

              <div className="card-middle">
                <div className="chip">
                  <span />
                  <span />
                  <span />
                  <span />
                </div>
                <span className="contactless">)))</span>
              </div>

              <div className="card-bottom">
                <div>
                  <small>YOUR WORLD. YOUR WAY.</small>
                  <strong>Aurora Signature</strong>
                </div>
                <span className="card-circles">
                  <i />
                  <i />
                </span>
              </div>
            </div>

            <div className="floating-note">
              <span className="floating-icon">✳</span>
              <div>
                <strong>Banking, made simpler.</strong>
                <small>Everyday finance, reimagined.</small>
              </div>
            </div>

            <div className="visual-caption">
              <span>01 /</span> A NEW PERSPECTIVE ON BANKING
            </div>
          </div>
        </section>

        <section className="services section" id="services">
          <div className="section-heading">
            <div>
              <div className="eyebrow">BANKING THAT FITS YOUR LIFE</div>
              <h2>Everything you need.<br />Nothing you don't.</h2>
            </div>
            <p>
              From everyday transactions to long-term goals,
              discover banking designed to make life easier.
            </p>
          </div>

          <div className="service-grid">
            {services.map((service) => (
              <article className="service-card" key={service.title}>
                <div className="service-icon">{service.icon}</div>
                <h3>{service.title}</h3>
                <p>{service.description}</p>
                <a href="/support" aria-label={`Get help with ${service.title}`}>
                  Learn more <span>↗</span>
                </a>
              </article>
            ))}
          </div>
        </section>

        <section className="about section" id="about">
          <div className="about-symbol">A.</div>
          <div>
            <div className="eyebrow">A BANK THAT LISTENS</div>
            <h2>More than banking.<br />A relationship built on trust.</h2>
            <p>
              We believe banking should feel clear, approachable,
              and personal. Every question deserves attention,
              and every customer deserves to be heard.
            </p>
          </div>
        </section>

        <section className="support-section" id="support">
          <div>
            <div className="eyebrow">HERE WHEN YOU NEED US</div>
            <h2>Have a question?<br />Let's sort it out.</h2>
            <p>
              Payment trouble, card questions, or something else?
              Our customer support team is here to help.
            </p>
          </div>

          <a className="support-button" href="/support">
            Contact Support <span>↗</span>
          </a>
        </section>
      </main>

      <footer className="footer">
        <a className="brand footer-brand" href="#home">
          <span className="brand-mark">A</span>
          <span>
            <strong>AURORA</strong>
            <small>B A N K</small>
          </span>
        </a>

        <p>Banking for your next chapter.</p>
        <span>© 2026 Aurora Bank · Demo website</span>
      </footer>
    </div>
  );
}

export default App;
