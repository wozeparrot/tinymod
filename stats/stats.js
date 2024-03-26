function main() {
  // connect to websocket
  const socket = new WebSocket("ws://127.0.0.1:10000");
  console.log("Connecting to websocket");

  // charts
  const charts = {};

  socket.onmessage = (event) => {
    // split event.data on first space
    // first part is status code
    // second part is data
    const status = event.data[0];
    const raw_data = event.data.slice(2);
    if (status !== "0") {
      console.error("Error: ", raw_data);
      return;
    }
    const data = JSON.parse(raw_data);

    charts[`${data.filename}-${data.system}`].update({
      "series": [data.benchmarks],
    });
    charts[`${data.filename}-${data.system}`].seq = 0;
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      const filename = entry.target.getAttribute("data-filename");
      const system = entry.target.getAttribute("data-system");

      if (entry.isIntersecting) {
        // check if there is a chart already
        if (!entry.target.hasAttribute("data-charted")) {
          charts[`${filename}-${system}`] = new Chartist.Line(
            `#chart-${filename.replace(/\.[^/.]+$/, "")}-${system}`,
            {},
            {
              showPoint: false,
              showLine: true,
              lineSmooth: false,
              axisX: {
                type: Chartist.AutoScaleAxis,
                onlyInteger: true,
              },
            },
          );
          charts[`${filename}-${system}`].seq = 0;
          charts[`${filename}-${system}`].on("draw", (data) => {
            data.element.animate({
              opacity: {
                begin: charts[`${filename}-${system}`].seq++,
                dur: 1000,
                from: 0,
                to: 1,
              },
            });
          });
          socket.send(`get-benchmark ${filename} ${system} 0`);

          entry.target.setAttribute("data-charted", true);
        }
      }
      observer.observe(entry.target);
    });
  }, {
    threshold: 0.25,
  });

  socket.onopen = () => {
    console.log("Connected to websocket");
    for (const card of document.querySelectorAll(".stat-card")) {
      observer.observe(card);
    }
  };
}

main();
