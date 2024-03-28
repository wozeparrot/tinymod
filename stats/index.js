function main() {
  // last-n slider
  const last_n_slider = document.querySelector(".last-n-slider");
  const last_n = document.querySelector(".last-n");
  if (last_n_slider.value == 0) {
    last_n.textContent = "All";
  } else {
    last_n.textContent = last_n_slider.value;
  }

  // back to top button
  const back_to_top = document.querySelector(".back-to-top");
  back_to_top.addEventListener("click", () => {
    window.scrollTo({
      top: 0,
      behavior: "smooth",
    });
  });

  // connect to websocket
  const socket = new WebSocket("wss://tinymod.dev:10000");
  console.log("Connecting to websocket");

  // charts
  const charts = {};

  // last-n slider event listener
  last_n_slider.addEventListener("input", (event) => {
    if (event.target.value == 0) {
      last_n.textContent = "All";
    } else {
      last_n.textContent = event.target.value;
    }

    for (const card of document.querySelectorAll(".stat-card")) {
      if (card.hasAttribute("data-charted")) {
        // const filename = card.getAttribute("data-filename");
        // const system = card.getAttribute("data-system");
        // socket.send(
        //   `get-benchmark ${filename} ${system} ${event.target.value}`,
        // );
        observer.unobserve(card);
        observer.observe(card);
        card.removeAttribute("data-charted");
      }
    }
  });

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

    if ("benchmarks" in data) {
      // generate integer only chart ticks for the x axis
      const x_ticks = [];
      const low = Math.floor(data.benchmarks[0].x / 10) * 10;
      const high =
        Math.ceil(data.benchmarks[data.benchmarks.length - 1].x / 10) *
        10;
      const divisor = (high - low) / 10;
      for (let i = low; i < high; i += divisor) {
        const i_10 = i;
        if (
          i_10 < data.benchmarks[0].x ||
          i_10 > data.benchmarks[data.benchmarks.length - 1].x
        ) continue;
        x_ticks.push(i_10);
      }

      // update chart
      charts[`${data.filename}-${data.system}`].update({
        series: [data.benchmarks],
      }, {
        showPoint: (data.benchmarks.length <= 100) ? true : false,
        showLine: true,
        showArea: true,
        lineSmooth: false,
        axisX: {
          type: Chartist.FixedScaleAxis,
          ticks: x_ticks,
          high: data.benchmarks[data.benchmarks.length - 1].x,
          low: data.benchmarks[0].x,
        },
      });
    } else if ("commit" in data) {
      const commitElem = document.querySelector("#curr-commit");
      commitElem.textContent = data.commit.slice(0, 7);
      commitElem.href =
        `https://github.com/tinygrad/tinygrad/commit/${data.commit}`;
    }
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
          );
          charts[`${filename}-${system}`].on("draw", (data) => {
            if (data.type === "line" || data.type === "area") {
              data.element.animate({
                d: {
                  begin: 2000 * data.index,
                  dur: 1000,
                  from: data.path.clone().scale(1, 0).translate(
                    0,
                    data.chartRect.height(),
                  ).stringify(),
                  to: data.path.clone().stringify(),
                  easing: Chartist.Svg.Easing.easeOutQuint,
                },
              });
            }
          });
          socket.send(
            `get-benchmark ${filename} ${system} ${last_n_slider.value}`,
          );

          entry.target.setAttribute("data-charted", true);
        }
      }
    });
  }, {
    threshold: 0.25,
  });

  socket.onopen = () => {
    console.log("Connected to websocket");
    socket.send("get-commit");
    for (const card of document.querySelectorAll(".stat-card")) {
      observer.observe(card);
    }
  };
}

main();
