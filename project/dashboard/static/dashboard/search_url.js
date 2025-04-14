function goToFeedPage(event) {
  let form = document.getElementById("search_feeds");
  let select = form.querySelector("select");
  let value = select.value;

  window.location.href = "/feeds/" + value;
  event.preventDefault();
}

const form = document.getElementById("search_feeds");
form.addEventListener("submit", goToFeedPage);
